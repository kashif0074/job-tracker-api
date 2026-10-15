import json
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

JobStatus = Literal["saved", "applied", "interview", "offer", "rejected"]


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    location: str | None = None
    status: JobStatus = "saved"
    technologies: list[str] = Field(default_factory=list)
    job_url: str | None = None
    application_deadline: date | None = None


class JobUpdate(BaseModel):
    """All fields optional — send only what you want to change."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    company: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = None
    status: JobStatus | None = None
    technologies: list[str] | None = None
    job_url: str | None = None
    application_deadline: date | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    company: str
    location: str | None
    status: JobStatus
    technologies: list[str] = Field(default_factory=list)
    job_url: str | None
    application_deadline: date | None
    created_at: datetime

    @field_validator("technologies", mode="before")
    @classmethod
    def parse_technologies(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except json.JSONDecodeError:
                return [t.strip() for t in v.split(",") if t.strip()]
        return v


class JobListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[JobResponse]