from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class Project(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
