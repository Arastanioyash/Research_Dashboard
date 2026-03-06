from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.refresh_job import RefreshJob
from app.schemas.refresh_job import RefreshJobResponse, RefreshRequest
from app.services.refresh_pipeline import run_refresh_job

router = APIRouter(prefix="/projects", tags=["refresh"])


async def require_admin(x_admin: str | None = Header(default=None)) -> None:
    if x_admin != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.post("/{id}/refresh", response_model=RefreshJobResponse, dependencies=[Depends(require_admin)])
async def trigger_refresh(
    id: uuid.UUID,
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshJob:
    return await run_refresh_job(
        db=db,
        project_id=id,
        model_version=payload.model_version,
        raw_csv=payload.raw_csv,
    )


@router.get("/{id}/refresh-jobs", response_model=list[RefreshJobResponse])
async def list_refresh_jobs(id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[RefreshJob]:
    statement = select(RefreshJob).where(RefreshJob.project_id == id).order_by(desc(RefreshJob.created_at))
    return list((await db.execute(statement)).scalars().all())


@router.get("/{id}/refresh-jobs/{job_id}", response_model=RefreshJobResponse)
async def get_refresh_job(id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> RefreshJob:
    statement = select(RefreshJob).where(RefreshJob.project_id == id, RefreshJob.id == job_id)
    job = (await db.execute(statement)).scalars().first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh job not found")
    return job
