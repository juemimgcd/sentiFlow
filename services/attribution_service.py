from collections import Counter
import json
from typing import Any

import httpx

from conf.settings import settings
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
    """负责基于主题分析结果进行问题归因、风险评分和代表样本筛选。"""

    category_values = tuple(category.value for category in IssueCategory)

    def classify_issue(self, item: SampleTopicResult) -> tuple[IssueCategory, str]:
        analysis = self.analyze_issue(item)
        return analysis["issue_category"], analysis["issue_reason"]

    # 调用 LLM 将 Day 7 内容结构结果归因为稳定问题类别。
    def analyze_issue(self, item: SampleTopicResult) -> dict[str, Any]:
        if not settings.LLM_BASE_URL or not settings.LLM_MODEL_NAME:
            raise RuntimeError("缺少 LLM_BASE_URL 或 LLM_MODEL_NAME，无法执行问题归因")

        response = httpx.post(
            self._chat_completions_url(),
            headers=self._build_headers(),
            json={
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是舆情分析助手。请只输出 JSON，不要输出 Markdown。"
                            "JSON 字段必须包含 issue_category、issue_reason。"
                            "issue_category 必须是以下英文 code 之一："
                            f"{', '.join(self.category_values)}。"
                            "这些 code 是稳定业务分类，不要按固定中文关键词命中规则判断。"
                            "issue_reason 用一句中文说明归因依据，不要只复述原评论。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "根据评论内容、情感标签和 Day 7 内容结构结果，判断最合适的问题类别。\n"
                            f"评论：{item.content_clean}\n"
                            f"情感：{item.sentiment_label.value}\n"
                            f"Day 7 主题：{item.topic_label}\n"
                            f"关键词：{item.keywords}\n"
                            f"风险词：{item.risk_keywords}"
                        ),
                    },
                ],
                "temperature": 0,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_model_json(content)

    # 生成 OpenAI 兼容的 chat completions 地址。
    @staticmethod
    def _chat_completions_url() -> str:
        base_url = settings.LLM_BASE_URL.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    # 构造 LLM 请求头。
    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if settings.DASHSCOPE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.DASHSCOPE_API_KEY}"
        return headers

    # 解析模型返回的问题归因 JSON。
    @staticmethod
    def _parse_model_json(content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()

        payload = json.loads(content)
        raw_category = str(payload.get("issue_category") or IssueCategory.general.value).strip()
        try:
            issue_category = IssueCategory(raw_category)
        except ValueError:
            issue_category = IssueCategory.general

        return {
            "issue_category": issue_category,
            "issue_reason": str(payload.get("issue_reason") or "模型未返回明确归因原因"),
        }

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
        results = []
        for item in topic_results:
            category, reason = self.classify_issue(item)
            risk_score = self.score_risk(item, category)
            results.append(
                SampleIssueAttribution(
                    sample_id=item.sample_id,
                    content_clean=item.content_clean,
                    sentiment_label=item.sentiment_label,
                    topic_label=item.topic_label,
                    issue_category=category,
                    issue_reason=reason,
                    risk_score=risk_score,
                    keywords=item.keywords,
                    risk_keywords=item.risk_keywords,
                )
            )
        return results

    def build_category_summary(
        self,
        task_id: str,
        attributions: list[SampleIssueAttribution],
    ) -> IssueCategorySummary:
        counter = Counter(item.issue_category for item in attributions)
        negative_issue_count = sum(
            1 for item in attributions if item.sentiment_label == SentimentLabel.negative
        )
        top_issue_categories = [category for category, _ in counter.most_common(5)]
        return IssueCategorySummary(
            task_id=task_id,
            category_distribution=dict(counter),
            negative_issue_count=negative_issue_count,
            top_issue_categories=top_issue_categories,
        )

    def select_representative_samples(
        self,
        attributions: list[SampleIssueAttribution],
        limit: int = 5,
    ) -> list[RepresentativeSample]:
        sorted_items = sorted(
            attributions,
            key=lambda item: (
                item.sentiment_label == SentimentLabel.negative,
                item.risk_score,
                len(item.risk_keywords),
            ),
            reverse=True,
        )

        selected = []
        used_categories = set()
        for item in sorted_items:
            if len(selected) >= limit:
                break
            if item.issue_category in used_categories and len(used_categories) < limit:
                continue
            used_categories.add(item.issue_category)
            selected.append(
                RepresentativeSample(
                    sample_id=item.sample_id,
                    content_clean=item.content_clean,
                    issue_category=item.issue_category,
                    sentiment_label=item.sentiment_label,
                    risk_score=item.risk_score,
                    reason=item.issue_reason,
                )
            )

        if len(selected) < limit:
            selected_ids = {item.sample_id for item in selected}
            for item in sorted_items:
                if len(selected) >= limit:
                    break
                if item.sample_id in selected_ids:
                    continue
                selected.append(
                    RepresentativeSample(
                        sample_id=item.sample_id,
                        content_clean=item.content_clean,
                        issue_category=item.issue_category,
                        sentiment_label=item.sentiment_label,
                        risk_score=item.risk_score,
                        reason=item.issue_reason,
                    )
                )
        return selected

    def run_issue_attribution(
        self,
        task_id: str,
        topic_results: list[SampleTopicResult],
    ) -> IssueAttributionResponse:
        attributions = self.build_sample_attributions(topic_results)
        summary = self.build_category_summary(task_id=task_id, attributions=attributions)
        representative_samples = self.select_representative_samples(attributions)
        return IssueAttributionResponse(
            task_id=task_id,
            summary=summary,
            representative_samples=representative_samples,
            preview_results=attributions[:5],
        )
