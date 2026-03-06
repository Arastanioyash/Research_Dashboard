from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import StrictModel


class BannerSpecModel(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    question_ids: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class NetDefinitionModel(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    buckets: dict[str, list[str]] = Field(default_factory=dict)


class PageSpecModel(StrictModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    layout: dict[str, Any] = Field(default_factory=dict)


class PageQuestionMappingRequest(StrictModel):
    question_ids: list[str] = Field(default_factory=list)


class ListResponse(StrictModel):
    items: list[Any]
