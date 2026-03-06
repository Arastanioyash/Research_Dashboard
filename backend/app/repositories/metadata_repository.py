from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BannerSpec, NetDef, PageQuestionMap, PageSpec, Project


@dataclass
class MetadataPayload:
    banner_spec: dict[str, Any] | None
    net_definitions: list[dict[str, Any]]
    pages: list[dict[str, Any]]


class PostgresMetadataRepository:
    """Metadata persistence backed by Postgres via SQLAlchemy."""

    def __init__(self, session: Session):
        self.session = session

    def get_project_metadata(self, project_id: str) -> MetadataPayload:
        banner = self.session.scalar(select(BannerSpec).where(BannerSpec.project_id == project_id))
        net_defs = self.session.scalars(select(NetDef).where(NetDef.project_id == project_id)).all()
        page_specs = self.session.scalars(select(PageSpec).where(PageSpec.project_id == project_id)).all()

        page_payload = []
        for page in page_specs:
            questions = self.session.scalars(
                select(PageQuestionMap)
                .where(PageQuestionMap.page_spec_id == page.id)
                .order_by(PageQuestionMap.display_order)
            ).all()
            page_payload.append(
                {
                    "id": page.id,
                    "slug": page.slug,
                    "title": page.title,
                    "layout": page.layout,
                    "question_map": [
                        {
                            "question_key": q.question_key,
                            "display_order": q.display_order,
                        }
                        for q in questions
                    ],
                }
            )

        return MetadataPayload(
            banner_spec=banner.spec if banner else None,
            net_definitions=[{"id": n.id, "name": n.name, "definition": n.definition} for n in net_defs],
            pages=page_payload,
        )

    def upsert_project(self, project_id: str, name: str, description: str | None = None) -> Project:
        project = self.session.get(Project, project_id)
        if project is None:
            project = Project(id=project_id, name=name, description=description)
            self.session.add(project)
        else:
            project.name = name
            project.description = description

        self.session.commit()
        self.session.refresh(project)
        return project

    def upsert_banner_spec(self, project_id: str, spec: dict[str, Any]) -> BannerSpec:
        banner = self.session.scalar(select(BannerSpec).where(BannerSpec.project_id == project_id))
        if banner is None:
            banner = BannerSpec(project_id=project_id, spec=spec)
            self.session.add(banner)
        else:
            banner.spec = spec

        self.session.commit()
        self.session.refresh(banner)
        return banner
