from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def upsert_job_graph(job_id: int, title: str, company: str, skills: dict):
    """
    Store job + skills as a graph in Neo4j.
    Creates relationships: (Job)-[:REQUIRES]->(Skill), (Job)-[:POSTED_BY]->(Company)
    """
    skill_names = (
        skills.get("languages", [])
        + skills.get("frameworks", [])
        + skills.get("ai_tools", [])
    )

    with driver.session() as session:
        session.run(
            """
            MERGE (j:Job {id: $job_id})
            SET j.title = $title
            MERGE (c:Company {name: $company})
            MERGE (j)-[:POSTED_BY]->(c)
            WITH j
            UNWIND $skills AS skill_name
                MERGE (s:Skill {name: skill_name})
                MERGE (j)-[:REQUIRES]->(s)
            """,
            job_id=job_id,
            title=title,
            company=company,
            skills=skill_names,
        )


def get_related_skills(skill_name: str, limit: int = 10) -> list[str]:
    """
    GraphRAG: Given a skill, find other skills that appear in jobs
    that also require this skill.
    """
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s1:Skill {name: $skill})<-[:REQUIRES]-(j:Job)-[:REQUIRES]->(s2:Skill)
            WHERE s1 <> s2
            RETURN s2.name AS skill, count(j) AS frequency
            ORDER BY frequency DESC
            LIMIT $limit
            """,
            skill=skill_name,
            limit=limit,
        )
        return [record["skill"] for record in result]