from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import require_project_permission
from app.models.project import ProjectMembership

router = APIRouter(prefix="/projects", tags=["projects"])
CanRead = Annotated[ProjectMembership, Depends(require_project_permission("read"))]
CanWrite = Annotated[ProjectMembership, Depends(require_project_permission("write"))]


@router.get("/{project_id}/reports")
def get_project_reports(_: CanRead):
    return {"status": "ok", "access": "read"}


@router.post("/{project_id}/reports")
def create_project_report(_: CanWrite):
    return {"status": "ok", "access": "write"}


@router.put("/{project_id}/reports/{report_id}")
def update_project_report(_: CanWrite, report_id: int):
    return {"status": "ok", "access": "write", "report_id": report_id}
