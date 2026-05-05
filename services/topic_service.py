from collections import Counter

from shcemas.preprocess_schema import NormalizedSample
from shcemas.sentiment_schema import SampleSentimentResult, SentimentLabel
from shcemas.topic_schema import SampleTopicResult, TaskKeywordSummary, TaskTopicSummary, TopicAnalysisResponse


class TopicService:
    def extract_keywords(self, sample: NormalizedSample):
        # 你要做的事：
        # 1. 读取单条标准样本文本
        # 2. 提取关键词
        # 3. 提取风险词
        text = sample.content_clean
        candidate_keywords = ["物流", "价格", "包装", "服务", "质量", "功能", "售后", "发货"]
        risk_seed = {"投诉", "失望", "损坏", "延迟", "故障", "不好"}

        keywords = [word for word in candidate_keywords if word in text]
        risk_keywords = [word for word in keywords if word in {"物流", "质量", "服务"}]

        if any(seed in text for seed in risk_seed):
            risk_keywords = sorted(set(risk_keywords + ["负向风险表达"]))

        return keywords, risk_keywords


    def classify_topic(
            self,
            sample: NormalizedSample,
            keywords: list[str],
    ) -> tuple[str, str]:
        text = sample.content_clean

        if any(word in keywords or word in text for word in ["物流", "发货"]):
            return "物流履约", "命中物流与发货相关表达"
        if any(word in keywords or word in text for word in ["价格", "优惠"]):
            return "价格体验", "命中价格与优惠相关表达"
        if any(word in keywords or word in text for word in ["质量", "损坏"]):
            return "质量问题", "命中质量与损坏相关表达"
        if any(word in keywords or word in text for word in ["服务", "售后"]):
            return "服务售后", "命中服务与售后相关表达"
        return "通用反馈", "未命中更细主题，先归入通用反馈"

    def build_sample_topic_results(
            self,
            samples: list[NormalizedSample],
            sentiment_map: dict[str, SampleSentimentResult],
    ) -> list[SampleTopicResult]:
        results = []
        for sample in samples:
            keywords, risk_keywords = self.extract_keywords(sample)
            topic_label, topic_reason = self.classify_topic(sample, keywords)

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
                    keywords=keywords,
                    risk_keywords=risk_keywords,
                    topic_label=topic_label,
                    topic_reason=topic_reason,
                )
            )
        return results

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







