from __future__ import annotations

from enum import Enum

from pydantic import Field

from .common import StrictModel


class Metric(str, Enum):
    count = "count"
    percent = "percent"


class ResultQueryParams(StrictModel):
    question_id: str = Field(min_length=1)
    banner_id: str | None = None
    filters: str | None = None
    metric: Metric = Metric.count


class TidyResultRow(StrictModel):
    question_id: str
    answer: str
    banner_value: str | None = None
    value: float


class ResultResponse(StrictModel):
    project_id: str
    metric: Metric
    rows: list[TidyResultRow]
