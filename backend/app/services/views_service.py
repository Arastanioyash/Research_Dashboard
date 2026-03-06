from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session

from app.models.saved_view import SavedView
from app.schemas.views import SavedViewCreate, SavedViewUpdate


@dataclass(slots=True)
class UserContext:
    id: int
    is_admin: bool = False
    can_view_projects: set[int] = field(default_factory=set)


class ViewsService:
    """Service layer for persisted project saved views."""

    def __init__(self, session: Session):
        self.session = session

    def create_view(self, *, project_id: int, payload: SavedViewCreate, user: UserContext) -> SavedView:
        self._require_project_view_access(project_id, user)

        entity = SavedView(
            project_id=project_id,
            name=payload.name,
            created_by=user.id,
            page_id=payload.page_id,
            question_id=payload.question_id,
            banner_id=payload.banner_id,
            filter_state_json=payload.filter_state_json,
            ui_state_json=payload.ui_state_json,
        )
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def list_views(self, *, project_id: int, user: UserContext) -> list[SavedView]:
        self._require_project_view_access(project_id, user)

        stmt: Select[tuple[SavedView]] = (
            select(SavedView)
            .where(SavedView.project_id == project_id)
            .order_by(SavedView.created_at.desc(), SavedView.id.desc())
        )
        return list(self.session.scalars(stmt))

    def get_view(self, *, project_id: int, view_id: int, user: UserContext) -> SavedView:
        self._require_project_view_access(project_id, user)
        entity = self._load_view(project_id=project_id, view_id=view_id)
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found")
        return entity

    def update_view(
        self,
        *,
        project_id: int,
        view_id: int,
        payload: SavedViewUpdate,
        user: UserContext,
    ) -> SavedView:
        entity = self.get_view(project_id=project_id, view_id=view_id, user=user)
        self._require_mutation_access(entity, user)

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(entity, field, value)

        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_view(self, *, project_id: int, view_id: int, user: UserContext) -> None:
        entity = self.get_view(project_id=project_id, view_id=view_id, user=user)
        self._require_mutation_access(entity, user)

        self.session.execute(delete(SavedView).where(SavedView.id == entity.id))
        self.session.commit()

    def _load_view(self, *, project_id: int, view_id: int) -> SavedView | None:
        stmt = select(SavedView).where(SavedView.id == view_id, SavedView.project_id == project_id)
        return self.session.scalars(stmt).first()

    @staticmethod
    def _require_mutation_access(entity: SavedView, user: UserContext) -> None:
        if user.is_admin or entity.created_by == user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator or an admin can modify this saved view",
        )

    @staticmethod
    def _require_project_view_access(project_id: int, user: UserContext) -> None:
        if user.is_admin or project_id in user.can_view_projects:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this project")


def normalize_project_scope(project_ids: Iterable[int]) -> set[int]:
    return {int(project_id) for project_id in project_ids}

