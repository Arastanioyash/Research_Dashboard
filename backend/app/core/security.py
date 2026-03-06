from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import JWT_ALGORITHM, JWT_AUDIENCE, JWT_SECRET
from app.db.session import get_db
from app.models.auth import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenPayload(dict):
    @property
    def subject(self) -> str | None:
        return self.get("sub")


def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT claims used by API dependencies."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            options={"require": ["exp", "sub", "aud"]},
        )
        return TokenPayload(payload)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    payload = decode_token(token)
    if not payload.subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token subject")

    stmt = select(User).where(User.email == payload.subject, User.is_active.is_(True))
    user = db.scalar(stmt)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(role_name: str):
    def dependency(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        role_stmt = (
            select(UserRole)
            .join(UserRole.role)
            .where(UserRole.user_id == user.id)
            .where(UserRole.role.has(name=role_name))
        )
        if not db.scalar(role_stmt):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency
