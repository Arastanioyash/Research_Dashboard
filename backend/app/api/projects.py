from fastapi import APIRouter, HTTPException, status

from app.models.project import Project, ProjectCreate
from app.services.metadata import metadata_service

router = APIRouter()


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate) -> Project:
    return metadata_service.create_project(payload)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = metadata_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
