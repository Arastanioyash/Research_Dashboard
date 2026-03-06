from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import StrictModel


class MetadataUploadRequest(StrictModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class BannerMetadataUploadRequest(StrictModel):
    banner_metadata: dict[str, Any] = Field(default_factory=dict)


class UploadResponse(StrictModel):
    project_id: str
    message: str
    row_count: int | None = None
