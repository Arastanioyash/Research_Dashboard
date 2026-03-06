from __future__ import annotations

import csv
import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import uuid

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_job import RefreshJob, RefreshJobStatus

logger = logging.getLogger(__name__)

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage"
BANNERS_FILE = "banners.json"


def _project_root(project_id: uuid.UUID) -> Path:
    return STORAGE_ROOT / "projects" / str(project_id)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _persist_or_resolve_raw(project_id: uuid.UUID, raw_csv: str | None) -> tuple[Path, str]:
    raw_dir = _project_root(project_id) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if raw_csv is not None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        raw_path = raw_dir / f"{timestamp}.csv"
        raw_path.write_text(raw_csv, encoding="utf-8")
        return raw_path, _hash_text(raw_csv)

    raw_files = sorted(raw_dir.glob("*.csv"))
    if not raw_files:
        raise ValueError("No raw CSV found to refresh from.")

    latest = raw_files[-1]
    return latest, _hash_text(latest.read_text(encoding="utf-8"))


def _run_transformation_engine(raw_path: Path, project_id: uuid.UUID, model_version: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with raw_path.open("r", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        for row in reader:
            row["_project_id"] = str(project_id)
            row["_model_version"] = model_version
            rows.append(row)

    transformed_dir = _project_root(project_id) / "transformed"
    transformed_dir.mkdir(parents=True, exist_ok=True)
    transformed_path = transformed_dir / f"{model_version}.json"
    transformed_path.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def _invalidate_prior_cache(project_id: uuid.UUID, model_version: str) -> None:
    cache_root = _project_root(project_id) / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    for child in cache_root.iterdir():
        if child.is_dir() and child.name != model_version:
            for file in child.rglob("*"):
                if file.is_file():
                    file.unlink()
            for directory in sorted([d for d in child.rglob("*") if d.is_dir()], reverse=True):
                directory.rmdir()
            child.rmdir()


def _precompute_common_cuts(project_id: uuid.UUID, model_version: str, rows: list[dict[str, Any]]) -> None:
    project_root = _project_root(project_id)
    cache_dir = project_root / "cache" / model_version
    cache_dir.mkdir(parents=True, exist_ok=True)

    cuts: dict[str, Any] = {"overall": {"count": len(rows)}}

    banners_path = project_root / BANNERS_FILE
    if banners_path.exists():
        banners = json.loads(banners_path.read_text(encoding="utf-8"))
        for banner in banners:
            key = banner.get("key")
            if key:
                cuts[key] = {}
                for row in rows:
                    value = row.get(key, "__missing__")
                    cuts[key][value] = cuts[key].get(value, 0) + 1

    (cache_dir / "cuts.json").write_text(json.dumps(cuts), encoding="utf-8")


async def _get_existing_job(
    db: AsyncSession,
    project_id: uuid.UUID,
    source_hash: str,
    model_version: str,
) -> RefreshJob | None:
    statement: Select[tuple[RefreshJob]] = (
        select(RefreshJob)
        .where(
            RefreshJob.project_id == project_id,
            RefreshJob.source_hash == source_hash,
            RefreshJob.model_version == model_version,
        )
        .order_by(desc(RefreshJob.created_at))
        .limit(1)
    )
    return (await db.execute(statement)).scalars().first()


async def run_refresh_job(
    db: AsyncSession,
    project_id: uuid.UUID,
    model_version: str,
    raw_csv: str | None,
) -> RefreshJob:
    raw_path, source_hash = _persist_or_resolve_raw(project_id, raw_csv)

    existing = await _get_existing_job(db, project_id, source_hash, model_version)
    if existing and existing.status in {RefreshJobStatus.pending, RefreshJobStatus.running, RefreshJobStatus.succeeded}:
        return existing

    job = RefreshJob(
        project_id=project_id,
        status=RefreshJobStatus.running,
        started_at=datetime.now(UTC),
        model_version=model_version,
        source_hash=source_hash,
        raw_csv_path=str(raw_path),
    )
    db.add(job)
    await db.flush()

    try:
        rows = _run_transformation_engine(raw_path, project_id, model_version)
        _invalidate_prior_cache(project_id, model_version)
        _precompute_common_cuts(project_id, model_version, rows)
        job.status = RefreshJobStatus.succeeded
        job.message = "Refresh completed successfully."
    except Exception as exc:
        logger.exception("Refresh job failed", extra={"project_id": project_id, "job_id": str(job.id)})
        job.status = RefreshJobStatus.failed
        job.message = f"Refresh failed: {exc}"
    finally:
        job.finished_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(job)

    return job
