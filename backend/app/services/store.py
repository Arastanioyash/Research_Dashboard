from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.models import BannerSpecModel, NetDefinitionModel, PageSpecModel, SchemaFieldModel


@dataclass
class ProjectState:
    csv_rows: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    banner_metadata: dict[str, Any] = field(default_factory=dict)
    schema: list[SchemaFieldModel] = field(default_factory=list)
    banner_specs: dict[str, BannerSpecModel] = field(default_factory=dict)
    net_definitions: dict[str, NetDefinitionModel] = field(default_factory=dict)
    page_specs: dict[str, PageSpecModel] = field(default_factory=dict)
    page_questions: dict[str, list[str]] = field(default_factory=dict)


class InMemoryStore:
    def __init__(self) -> None:
        self._projects: dict[str, ProjectState] = defaultdict(ProjectState)

    def project(self, project_id: str) -> ProjectState:
        return self._projects[project_id]


store = InMemoryStore()
