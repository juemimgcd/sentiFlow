from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawSample(BaseModel):
    """从数据集中读取到的原始文本样本。"""

    content: str
    published_at: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class NormalizedSample(BaseModel):
    """清洗、标准化并标记有效性的文本样本。"""

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
    """预处理后的样本数量、无效原因和预览汇总。"""

    raw_sample_count: int
    valid_sample_count: int
    invalid_sample_count: int
    invalid_reason_stats: dict[str, int] = Field(default_factory=dict)
    preview_samples: list[NormalizedSample] = Field(default_factory=list)
    processed_at: datetime


class PreprocessResponse(BaseModel):
    """预处理接口的统一响应结构。"""

    task_id: str
    dataset_id: str
    summary: PreprocessSummary
