from collections import Counter

from shcemas.attribution_schema import (
    IssueAttributionResponse,
    IssueCategory,
    IssueCategorySummary,
    RepresentativeSample,
    SampleIssueAttribution,
)
from shcemas.sentiment_schema import SentimentLabel
from shcemas.topic_schema import SampleTopicResult


class AttributionService:
    def classify_issue(self, item: SampleTopicResult) -> tuple[IssueCategory, str]:
        # 你要做的事：
        # 1. 读取 topic_label、keywords、risk_keywords 和 content_clean
        # 2. 按最小问题类别判断归因
        # 3. 返回问题类别和一条可读原因
        # 4. 不要在这里做任务级聚合
        text = item.content_clean
        keywords = set(item.keywords)
        risk_keywords = set(item.risk_keywords)
        topic = item.topic_label

        if topic == "物流履约" or keywords.intersection({"物流", "发货"}):
            return IssueCategory.logistics, "命中物流履约主题或发货相关关键词"
        if topic == "质量问题" or keywords.intersection({"质量", "包装"}) or "损坏" in text:
            return IssueCategory.quality, "命中质量、包装或损坏相关表达"
        if topic == "价格体验" or keywords.intersection({"价格", "优惠"}):
            return IssueCategory.price, "命中价格或优惠相关表达"
        if topic == "服务售后" or keywords.intersection({"服务", "售后"}):
            return IssueCategory.service, "命中服务或售后相关表达"
        if keywords.intersection({"功能"}):
            return IssueCategory.feature, "命中功能体验相关表达"
        if risk_keywords:
            return IssueCategory.general, "命中风险词但暂未归入更细问题类别"
        return IssueCategory.general, "未命中明确问题类别，先归入通用反馈"





    def score_risk(self, item: SampleTopicResult, category: IssueCategory) -> int:
        score = 0
        if item.sentiment_label == SentimentLabel.negative:
            score += 50
        if item.risk_keywords:
            score += min(len(item.risk_keywords) * 15, 30)
        if category != IssueCategory.general:
            score += 15
        if 8 <= len(item.content_clean) <= 120:
            score += 5
        return min(score, 100)

    def build_sample_attributions(
        self,
        topic_results: list[SampleTopicResult],
    ) -> list[SampleIssueAttribution]:
        # 你要做的事：
        # 1. 遍历样本级主题结果
        # 2. 调用 classify_issue 得到问题类别
        # 3. 调用 score_risk 得到风险分
        # 4. 组装样本级问题归因结果
        raise NotImplementedError

    def build_category_summary(
        self,
        task_id: str,
        attributions: list[SampleIssueAttribution],
    ) -> IssueCategorySummary:
        # 你要做的事：
        # 1. 统计每个问题类别数量
        # 2. 统计负向问题样本数量
        # 3. 取高频问题类别
        # 4. 组装任务级摘要
        raise NotImplementedError

    def select_representative_samples(
        self,
        attributions: list[SampleIssueAttribution],
        limit: int = 5,
    ) -> list[RepresentativeSample]:
        # 你要做的事：
        # 1. 优先选择负向样本
        # 2. 按风险分倒序
        # 3. 尽量保留不同问题类别
        # 4. 组装代表样本列表
        raise NotImplementedError

    def run_issue_attribution(
        self,
        task_id: str,
        topic_results: list[SampleTopicResult],
    ) -> IssueAttributionResponse:
        # 你要做的事：
        # 1. 先生成样本级问题归因
        # 2. 再生成任务级问题摘要
        # 3. 再筛选代表样本
        # 4. 最后组装统一响应
        raise NotImplementedError