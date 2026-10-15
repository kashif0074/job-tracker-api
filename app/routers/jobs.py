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