from enum import Enum

from pydantic import BaseModel, Field


class SentimentLabel(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class SampleSentimentResult(BaseModel):
    sample_id: str
    content_clean: str
    sentiment_label: SentimentLabel
    sentiment_score: float = Field(default=0.0)
    reason: str | None = None


class TaskSentimentSummary(BaseModel):
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
    task_id: str
    summary: TaskSentimentSummary
    preview_results: list[SampleSentimentResult] = Field(default_factory=list)