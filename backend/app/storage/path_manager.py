from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class PathManager:
    def __init__(self, base_data_dir: str | Path = "data"):
        self.base_data_dir = Path(base_data_dir)

    def ensure_project_dirs(self, project_id: str) -> dict[str, Path]:
        project_root = self.base_data_dir / "projects" / project_id
        raw_dir = project_root / "raw"
        model_dir = project_root / "model"

        raw_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)

        return {
            "project_root": project_root,
            "raw_dir": raw_dir,
            "model_dir": model_dir,
        }

    def ensure_model_version_dir(self, project_id: str, model_version: str | None = None) -> Path:
        paths = self.ensure_project_dirs(project_id)
        version = model_version or datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        version_dir = paths["model_dir"] / version
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir

    def schema_registry_path(self, project_id: str) -> Path:
        paths = self.ensure_project_dirs(project_id)
        return paths["model_dir"] / "schema_registry.json"
