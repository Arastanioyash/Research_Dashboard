from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.storage.path_manager import PathManager


class SchemaRegistryService:
    def __init__(self, path_manager: PathManager):
        self.path_manager = path_manager

    def load(self, project_id: str) -> dict[str, Any]:
        path = self.path_manager.schema_registry_path(project_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    def save(self, project_id: str, schema_registry: dict[str, Any]) -> Path:
        path = self.path_manager.schema_registry_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(schema_registry, indent=2, sort_keys=True))
        return path
