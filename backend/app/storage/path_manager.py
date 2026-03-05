from pathlib import Path

from app.core.config import get_settings


class PathManager:
    def __init__(self) -> None:
        self._root = Path(get_settings().data_root)

    def project_path(self, project_id: str) -> Path:
        return self._root / project_id

    def ensure_project_dirs(self, project_id: str) -> Path:
        project_root = self.project_path(project_id)
        (project_root / "raw").mkdir(parents=True, exist_ok=True)
        (project_root / "processed").mkdir(parents=True, exist_ok=True)
        (project_root / "exports").mkdir(parents=True, exist_ok=True)
        return project_root


path_manager = PathManager()
