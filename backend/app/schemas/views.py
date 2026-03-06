from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


REQUIRED_FILTER_KEYS = {"chips", "cross_filters", "selected_levels", "search_text"}


class SavedViewBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    page_id: int | None = None
    question_id: int | None = None
    banner_id: int | None = None
    filter_state_json: dict[str, Any]
    ui_state_json: dict[str, Any]

    @field_validator("filter_state_json")
    @classmethod
    def validate_filter_state_json(cls, value: dict[str, Any]) -> dict[str, Any]:
        missing_keys = REQUIRED_FILTER_KEYS.difference(value.keys())
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(
                "filter_state_json must include chips/cross-filters/selected levels/search text "
                f"(missing: {missing})"
            )

        if not isinstance(value.get("chips"), list):
            raise ValueError("filter_state_json.chips must be a list")
        if not isinstance(value.get("cross_filters"), (dict, list)):
            raise ValueError("filter_state_json.cross_filters must be a dict or list")
        if not isinstance(value.get("selected_levels"), list):
            raise ValueError("filter_state_json.selected_levels must be a list")
        if not isinstance(value.get("search_text"), str):
            raise ValueError("filter_state_json.search_text must be a string")

        return value


class SavedViewCreate(SavedViewBase):
    pass


class SavedViewUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    page_id: int | None = None
    question_id: int | None = None
    banner_id: int | None = None
    filter_state_json: dict[str, Any] | None = None
    ui_state_json: dict[str, Any] | None = None

    @field_validator("filter_state_json")
    @classmethod
    def validate_filter_state_json(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        return SavedViewBase.validate_filter_state_json(value)


class SavedViewRead(SavedViewBase):
    id: int
    project_id: int
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

