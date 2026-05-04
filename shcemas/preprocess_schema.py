from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawSample(BaseModel):
    content: str
    published_at: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class NormalizedSample(BaseModel):
    sample_id: str
    content_raw: str
    content_clean: str
    source_platform: str
    published_at: str | None = None
    language: str | None = None
    is_valid: bool = True
    invalid_reason: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class PreprocessSummary(BaseModel):
    raw_sample_count: int
    valid_sample_count: int
    invalid_sample_count: int
    invalid_reason_stats: dict[str, int] = Field(default_factory=dict)
    preview_samples: list[NormalizedSample] = Field(default_factory=list)
    processed_at: datetime


class PreprocessResponse(BaseModel):
    task_id: str
    dataset_id: str
    summary: PreprocessSummary