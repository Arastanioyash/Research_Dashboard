from __future__ import annotations

from app.repositories.metadata_repository import MetadataPayload, PostgresMetadataRepository


class MetadataService:
    """Service layer that delegates metadata operations to Postgres repositories."""

    def __init__(self, repository: PostgresMetadataRepository):
        self.repository = repository

    def get_project_metadata(self, project_id: str) -> MetadataPayload:
        return self.repository.get_project_metadata(project_id)

    def register_project(self, project_id: str, name: str, description: str | None = None) -> None:
        self.repository.upsert_project(project_id=project_id, name=name, description=description)

    def save_banner_spec(self, project_id: str, spec: dict) -> None:
        self.repository.upsert_banner_spec(project_id=project_id, spec=spec)
