from enum import Enum

from pydantic import BaseModel, Field


class SentimentLabel(str, Enum):
    """项目内部统一使用的情感标签。"""

    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class SampleSentimentResult(BaseModel):
    """单条样本的情感分类结果。"""

    sample_id: str
    content_clean: str
    sentiment_label: SentimentLabel
    sentiment_score: float = Field(default=0.0)
    reason: str | None = None


class TaskSentimentSummary(BaseModel):
    """任务级情感数量、占比和主导情绪汇总。"""

    task_id: str
    total_samples: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_ratio: float
    neutral_ratio: float
    negative_ratio: float
    dominant_sentiment: SentimentLabel


class SentimentResponse(BaseModel):
    """情感分析接口的统一响应结构。"""

    task_id: str
    summary: TaskSentimentSummary
    preview_results: list[SampleSentimentResult] = Field(default_factory=list)
