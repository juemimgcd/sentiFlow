from collections import Counter
import json
from typing import Any

import httpx

from conf.settings import settings
from shcemas.preprocess_schema import NormalizedSample
from shcemas.sentiment_schema import SampleSentimentResult, SentimentLabel
from shcemas.topic_schema import SampleTopicResult, TaskKeywordSummary, TaskTopicSummary, TopicAnalysisResponse


class TopicService:
    # 调用 LLM 获取单条样本的主题分析结果。
    def analyze_sample(self, sample: NormalizedSample) -> dict[str, Any]:
        if not settings.LLM_BASE_URL or not settings.LLM_MODEL_NAME:
            raise RuntimeError("缺少 LLM_BASE_URL 或 LLM_MODEL_NAME，无法执行主题分析")

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
                            "JSON 字段必须包含 keywords、risk_keywords、topic_label、topic_reason。"
                            "topic_label 用一个简短中文短语概括评论主题，不要照抄固定词表。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "分析下面这条中文评论，抽取关键词、风险词，并给出一个业务主题。\n"
                            f"评论：{sample.content_clean}"
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

    # 解析模型返回的 JSON 文本。
    @classmethod
    def _parse_model_json(cls, content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        payload = json.loads(content)
        topic_label = str(payload.get("topic_label") or "").strip() or "通用反馈"
        return {
            "keywords": cls._string_list(payload.get("keywords")),
            "risk_keywords": cls._string_list(payload.get("risk_keywords")),
            "topic_label": topic_label,
            "topic_reason": str(payload.get("topic_reason") or "模型未返回明确原因"),
        }

    # 将模型返回值规整为字符串列表。
    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []

        items = []
        for item in value:
            text = str(item).strip()
            if text and text not in items:
                items.append(text)
        return items[:10]

    # 生成样本级主题分析结果列表。
    def build_sample_topic_results(
            self,
            samples: list[NormalizedSample],
            sentiment_map: dict[str, SampleSentimentResult],
    ) -> list[SampleTopicResult]:
        results = []
        for sample in samples:
            analysis = self.analyze_sample(sample)

            sentiment_result = sentiment_map.get(sample.sample_id)
            sentiment_label = (
                sentiment_result.sentiment_label
                if sentiment_result is not None
                else SentimentLabel.neutral
            )

            results.append(
                SampleTopicResult(
                    sample_id=sample.sample_id,
                    content_clean=sample.content_clean,
                    sentiment_label=sentiment_label,
                    keywords=analysis["keywords"],
                    risk_keywords=analysis["risk_keywords"],
                    topic_label=analysis["topic_label"],
                    topic_reason=analysis["topic_reason"],
                )
            )
        return results

    # 汇总任务级关键词统计信息。
    def build_keyword_summary(
            self,
            task_id: str,
            results: list[SampleTopicResult],
    ) -> TaskKeywordSummary:
        counter = Counter()
        risk_words = set()

        for item in results:
            counter.update(item.keywords)
            risk_words.update(item.risk_keywords)

        top_keywords = [word for word, _ in counter.most_common(10)]

        return TaskKeywordSummary(
            task_id=task_id,
            top_keywords=top_keywords,
            risk_keywords=sorted(risk_words),
            keyword_frequency=dict(counter),
        )

    # 汇总任务级主题分布信息。
    def build_topic_summary(
            self,
            task_id: str,
            results: list[SampleTopicResult],
    ) -> TaskTopicSummary:
        counter = Counter(item.topic_label for item in results)
        dominant_topic = counter.most_common(1)[0][0] if counter else "通用反馈"

        return TaskTopicSummary(
            task_id=task_id,
            topic_distribution=dict(counter),
            dominant_topic=dominant_topic,
        )

    # 运行主题分析并组装统一响应。
    def run_topic_analysis(
            self,
            task_id: str,
            samples: list[NormalizedSample],
            sentiment_map: dict[str, SampleSentimentResult],
    ) -> TopicAnalysisResponse:
        results = self.build_sample_topic_results(samples=samples, sentiment_map=sentiment_map)
        keyword_summary = self.build_keyword_summary(task_id=task_id, results=results)
        topic_summary = self.build_topic_summary(task_id=task_id, results=results)
        return TopicAnalysisResponse(
            task_id=task_id,
            keyword_summary=keyword_summary,
            topic_summary=topic_summary,
            preview_results=results[:5],
        )


topic_service = TopicService()







