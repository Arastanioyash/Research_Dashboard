from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import StrictModel


class SchemaFieldModel(StrictModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    data_type: Literal["string", "number", "boolean", "date"]


class SchemaUpdateRequest(StrictModel):
    fields: list[SchemaFieldModel]


class SchemaResponse(StrictModel):
    project_id: str
    fields: list[SchemaFieldModel]
