from app.models.project import Project, ProjectCreate
from app.storage.path_manager import path_manager


class MetadataService:
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}

    def create_project(self, payload: ProjectCreate) -> Project:
        project = Project(name=payload.name, description=payload.description)
        path_manager.ensure_project_dirs(project.project_id)
        self._projects[project.project_id] = project
        return project

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)


metadata_service = MetadataService()
