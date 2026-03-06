from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    banner_spec: Mapped[BannerSpec | None] = relationship(back_populates="project", uselist=False)
    net_defs: Mapped[list[NetDef]] = relationship(back_populates="project", cascade="all, delete-orphan")
    page_specs: Mapped[list[PageSpec]] = relationship(back_populates="project", cascade="all, delete-orphan")
    saved_views: Mapped[list[SavedView]] = relationship(back_populates="project", cascade="all, delete-orphan")
    refresh_jobs: Mapped[list[RefreshJob]] = relationship(back_populates="project", cascade="all, delete-orphan")


class BannerSpec(TimestampMixin, Base):
    __tablename__ = "banner_spec"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    spec: Mapped[dict] = mapped_column(JSON, nullable=False)

    project: Mapped[Project] = relationship(back_populates="banner_spec")


class NetDef(TimestampMixin, Base):
    __tablename__ = "net_def"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)

    project: Mapped[Project] = relationship(back_populates="net_defs")


class PageSpec(TimestampMixin, Base):
    __tablename__ = "page_spec"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    layout: Mapped[dict] = mapped_column(JSON, nullable=False)

    project: Mapped[Project] = relationship(back_populates="page_specs")
    question_maps: Mapped[list[PageQuestionMap]] = relationship(
        back_populates="page_spec", cascade="all, delete-orphan"
    )


class PageQuestionMap(TimestampMixin, Base):
    __tablename__ = "page_question_map"
    __table_args__ = (
        UniqueConstraint("page_spec_id", "question_key", name="uq_page_question_map_page_question"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    page_spec_id: Mapped[str] = mapped_column(ForeignKey("page_spec.id", ondelete="CASCADE"), nullable=False)
    question_key: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    page_spec: Mapped[PageSpec] = relationship(back_populates="question_maps")


class SavedView(TimestampMixin, Base):
    __tablename__ = "saved_view"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)

    project: Mapped[Project] = relationship(back_populates="saved_views")
    user: Mapped[User] = relationship(back_populates="saved_views")


class RefreshJob(TimestampMixin, Base):
    __tablename__ = "refresh_job"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    details: Mapped[dict | None] = mapped_column(JSON)

    project: Mapped[Project] = relationship(back_populates="refresh_jobs")


class UserRole(Base):
    __tablename__ = "user_role_map"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role_map_user_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    saved_views: Mapped[list[SavedView]] = relationship(back_populates="user")
    roles: Mapped[list[Role]] = relationship(
        secondary="user_role_map",
        back_populates="users",
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    users: Mapped[list[User]] = relationship(
        secondary="user_role_map",
        back_populates="roles",
    )
