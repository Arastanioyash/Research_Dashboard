from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.refresh_job import RefreshJobStatus


class RefreshRequest(BaseModel):
    model_version: str = Field(min_length=1, max_length=64)
    raw_csv: str | None = None


class RefreshJobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: RefreshJobStatus
    started_at: datetime | None
    finished_at: datetime | None
    message: str | None
    model_version: str
    raw_csv_path: str

    class Config:
        from_attributes = True
