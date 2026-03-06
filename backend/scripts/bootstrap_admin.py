"""Seed the initial admin user from environment variables."""

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.core.config import ADMIN_EMAIL, ADMIN_PASSWORD
from app.db.session import SessionLocal
from app.models.auth import Role, User, UserRole


def run() -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be set to bootstrap admin user")

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if existing:
            return

        admin = User(email=ADMIN_EMAIL, password_hash=generate_password_hash(ADMIN_PASSWORD))
        db.add(admin)
        db.flush()

        role = db.scalar(select(Role).where(Role.name == "admin"))
        if role is None:
            role = Role(name="admin")
            db.add(role)
            db.flush()

        db.add(UserRole(user_id=admin.id, role_id=role.id))
        db.commit()


if __name__ == "__main__":
    run()
