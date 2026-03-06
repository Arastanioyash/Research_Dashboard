from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedView(Base):
    """A project-scoped persisted dashboard view state."""

    __tablename__ = "saved_view"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    page_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    banner_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filter_state_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ui_state_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

