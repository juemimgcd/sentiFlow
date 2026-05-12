from pydantic import BaseModel, Field

from shcemas.sentiment_schema import SentimentLabel


class SampleTopicResult(BaseModel):
    """单条样本的主题分析结果。"""

    sample_id: str
    content_clean: str
    sentiment_label: SentimentLabel
    keywords: list[str] = Field(default_factory=list)
    risk_keywords: list[str] = Field(default_factory=list)
    topic_label: str
    topic_reason: str | None = None


class TaskKeywordSummary(BaseModel):
    """任务级关键词和风险词汇总。"""

    task_id: str
    top_keywords: list[str] = Field(default_factory=list)
    risk_keywords: list[str] = Field(default_factory=list)
    keyword_frequency: dict[str, int] = Field(default_factory=dict)


class TaskTopicSummary(BaseModel):
    """任务级主题分布汇总。"""

    task_id: str
    topic_distribution: dict[str, int] = Field(default_factory=dict)
    dominant_topic: str


class TopicAnalysisResponse(BaseModel):
    """主题分析接口的统一响应结构。"""

    task_id: str
    keyword_summary: TaskKeywordSummary
    topic_summary: TaskTopicSummary
    preview_results: list[SampleTopicResult] = Field(default_factory=list)
