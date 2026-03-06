from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.project import ProjectMembership


def require_project_permission(permission: str):
    def dependency(
        project_id: Annotated[int, Path(ge=1)],
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> ProjectMembership:
        stmt = select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user.id,
        )
        membership = db.scalar(stmt)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

        allowed = {"read": {"read", "write"}, "write": {"write"}}
        if membership.permission not in allowed[permission]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return membership

    return dependency
