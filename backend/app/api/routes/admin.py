from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_role
from app.models.auth import User

router = APIRouter(prefix="/admin", tags=["admin"])
AdminUser = Annotated[User, Depends(require_role("admin"))]


@router.post("/upload")
def upload_dataset(_: AdminUser):
    return {"status": "ok", "action": "upload"}


@router.put("/schema")
def edit_schema(_: AdminUser):
    return {"status": "ok", "action": "schema-edit"}


@router.put("/banner")
def edit_banner(_: AdminUser):
    return {"status": "ok", "action": "banner-edit"}


@router.put("/net")
def edit_network(_: AdminUser):
    return {"status": "ok", "action": "net-edit"}


@router.put("/page")
def edit_page(_: AdminUser):
    return {"status": "ok", "action": "page-edit"}


@router.post("/refresh")
def refresh_cache(_: AdminUser):
    return {"status": "ok", "action": "refresh"}
