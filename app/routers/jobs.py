import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job
from app.models.user import User
from app.schemas.job import (
    JobCreate,
    JobListResponse,
    JobResponse,
    JobUpdate,
)
from app.services.agent import run_agent
from app.services.ai_service import get_embedding, extract_skills
from app.services.graph import upsert_job_graph, get_related_skills

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _serialize_technologies(techs: list[str]) -> str:
    return json.dumps(techs or [])


def _get_owned_job_or_404(db: Session, job_id: int, user: User) -> Job:
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user.id)
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: str | None = Query(default=None, alias="status"),
    location: str | None = Query(default=None),
    remote: bool | None = Query(default=None),
    technology: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    q = db.query(Job).filter(Job.user_id == current_user.id)

    if status_filter:
        q = q.filter(Job.status == status_filter)
    if location:
        q = q.filter(Job.location.ilike(f"%{location}%"))
    if remote is not None:
        q = q.filter(Job.remote == remote) if hasattr(Job, "remote") else q
    if technology:
        q = q.filter(Job.technologies.ilike(f"%{technology}%"))
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Job.title.ilike(like), Job.company.ilike(like)))

    total = q.count()
    items = (
        q.order_by(Job.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return JobListResponse(total=total, page=page, limit=limit, items=items)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = Job(
        user_id=current_user.id,
        title=payload.title,
        company=payload.company,
        location=payload.location,
        status=payload.status,
        technologies=_serialize_technologies(payload.technologies),
        job_url=payload.job_url,
        application_deadline=payload.application_deadline,
        description=payload.description,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_job_or_404(db, job_id, current_user)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user)
    data = payload.model_dump(exclude_unset=True)

    if "technologies" in data and data["technologies"] is not None:
        data["technologies"] = _serialize_technologies(data["technologies"])

    for field, value in data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user)
    db.delete(job)
    db.commit()
    return None


@router.post("/{job_id}/analyze")
def analyze_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user)

    if not job.description:
        raise HTTPException(status_code=400, detail="Job has no description to analyze")

    # 1. Extract skills via Groq LLM
    skills_dict = extract_skills(job.description)

    # 2. Generate local embedding
    text_to_embed = f"{job.title} at {job.company}. {job.description}"
    embedding_vector = get_embedding(text_to_embed)

    # 3. Save to database
    job.embedding = embedding_vector
    db.commit()
    db.refresh(job)

    return {
        "message": "Job analyzed successfully",
        "extracted_skills": skills_dict,
        "has_embedding": True,
    }


@router.get("/{job_id}/match")
def match_resume_to_job(
    job_id: int,
    resume_text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate the similarity between a resume and a job using pure Python cosine similarity.
    """
    job = _get_owned_job_or_404(db, job_id, current_user)

    if job.embedding is None:
        raise HTTPException(status_code=400, detail="Run POST /analyze on this job first")

    resume_embedding = get_embedding(resume_text)
    job_embedding = list(job.embedding)

    dot_product = sum(a * b for a, b in zip(resume_embedding, job_embedding))
    mag_a = sum(x * x for x in resume_embedding) ** 0.5
    mag_b = sum(x * x for x in job_embedding) ** 0.5

    if mag_a == 0 or mag_b == 0:
        raise HTTPException(status_code=500, detail="Zero-magnitude embedding error")

    similarity_score = float(dot_product / (mag_a * mag_b))

    return {
        "job_title": job.title,
        "match_score_percentage": round(similarity_score * 100, 2),
        "verdict": "Strong Match" if similarity_score > 0.8 else "Weak Match",
    }


@router.post("/agent/scrape-and-save")
async def agent_scrape_and_save(
    url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Agentic endpoint: scrapes a job URL, extracts skills, saves everything to DB and Neo4j.
    """
    prompt = f"""
    Your task is to:
    1. Scrape this job URL using the scrape_job tool: {url}
    2. Extract skills from the description using extract_skills_from_text.
    3. Return a summary with the title and the extracted skills.

    Do not guess. Use the tools.
    """

    result_text = await run_agent(prompt)

    # Try to extract the title from the agent's output
    # LLM outputs usually start with "Job Title: X" or similar
    first_line = result_text.split("\n")[0].strip()
    if ":" in first_line:
        detected_title = first_line.split(":", 1)[1].strip().strip("*").strip()
    else:
        detected_title = first_line.strip("*").strip()

    job = Job(
        user_id=current_user.id,
        title=detected_title[:200] if detected_title else "Auto-Scraped Job",
        company="Unknown",
        status="saved",
        description=result_text[:2000],
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "message": "Agent completed",
        "job_id": job.id,
        "agent_output": result_text[:500],
    }


@router.get("/graph/related-skills/{skill}")
def related_skills(
    skill: str,
    current_user: User = Depends(get_current_user),
):
    """
    GraphRAG: Returns skills that frequently co-occur with a given skill.
    """
    skills = get_related_skills(skill)
    return {"skill": skill, "related": skills}