from enum import Enum

from pydantic import BaseModel, Field

from shcemas.sentiment_schema import SentimentLabel


class IssueCategory(str, Enum):
    """问题归因使用的稳定业务类别。"""

    logistics = "logistics"
    quality = "quality"
    price = "price"
    service = "service"
    feature = "feature"
    general = "general"


class SampleIssueAttribution(BaseModel):
    """单条样本的问题归因和风险评分结果。"""

    sample_id: str
    content_clean: str
    sentiment_label: SentimentLabel
    topic_label: str
    issue_category: IssueCategory
    issue_reason: str
    risk_score: int = 0
    keywords: list[str] = Field(default_factory=list)
    risk_keywords: list[str] = Field(default_factory=list)


class RepresentativeSample(BaseModel):
    """用于结果展示的代表性问题样本。"""

    sample_id: str
    content_clean: str
    issue_category: IssueCategory
    sentiment_label: SentimentLabel
    risk_score: int
    reason: str


class IssueCategorySummary(BaseModel):
    """任务级问题类别分布和负向问题统计。"""

    task_id: str
    category_distribution: dict[IssueCategory, int] = Field(default_factory=dict)
    negative_issue_count: int = 0
    top_issue_categories: list[IssueCategory] = Field(default_factory=list)


class IssueAttributionResponse(BaseModel):
    """问题归因接口的统一响应结构。"""

    task_id: str
    summary: IssueCategorySummary
    representative_samples: list[RepresentativeSample] = Field(default_factory=list)
    preview_results: list[SampleIssueAttribution] = Field(default_factory=list)
