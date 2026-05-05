from pydantic import BaseModel, Field

from shcemas.sentiment_schema import SentimentLabel


class SampleTopicResult(BaseModel):
    sample_id: str
    content_clean: str
    sentiment_label: SentimentLabel
    keywords: list[str] = Field(default_factory=list)
    risk_keywords: list[str] = Field(default_factory=list)
    topic_label: str
    topic_reason: str | None = None


class TaskKeywordSummary(BaseModel):
    task_id: str
    top_keywords: list[str] = Field(default_factory=list)
    risk_keywords: list[str] = Field(default_factory=list)
    keyword_frequency: dict[str, int] = Field(default_factory=dict)


class TaskTopicSummary(BaseModel):
    task_id: str
    topic_distribution: dict[str, int] = Field(default_factory=dict)
    dominant_topic: str


class TopicAnalysisResponse(BaseModel):
    task_id: str
    keyword_summary: TaskKeywordSummary
    topic_summary: TaskTopicSummary
    preview_results: list[SampleTopicResult] = Field(default_factory=list)