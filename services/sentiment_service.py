from collections import Counter

from shcemas.preprocess_schema import NormalizedSample, PreprocessResponse
from shcemas.sentiment_schema import (
    SampleSentimentResult,
    SentimentLabel,
    SentimentResponse,
    TaskSentimentSummary,
)


class SentimentService:
    def classify_sample(self, sample: NormalizedSample) -> tuple[SentimentLabel, float, str]:
        # 你要做的事：
        # 1. 读取单条标准样本的文本
        # 2. 给出情感标签
        # 3. 给出一个最小分数
        # 4. 给出一个极简原因
        text = sample.content_clean
        negative_hits = ["差", "失望", "投诉", "慢", "问题", "不好"]
        positive_hits = ["好", "满意", "推荐", "喜欢", "不错", "赞"]

        if any(token in text for token in negative_hits):
            return SentimentLabel.negative, 0.82, "包含明显负向表达"
        if any(token in text for token in positive_hits):
            return SentimentLabel.positive, 0.79, "包含明显正向表达"
        return SentimentLabel.neutral, 0.55, "情绪表达较弱或偏描述性"

    def build_sample_results(self, samples: list[NormalizedSample]) -> list[SampleSentimentResult]:
        # 你要做的事：
        # 1. 遍历所有有效样本
        # 2. 对每条样本调用 classify_sample
        # 3. 组装成样本级情感结果列表
        results = []
        for sample in samples:
            label, score, summary = self.classify_sample(sample)
            results.append(
                SampleSentimentResult(
                    sample_id=sample.sample_id,
                    content_clean=sample.content_clean,
                    sentiment_label=label,
                    sentiment_score=score,
                    reason=summary
                )
            )

        return results

    def build_task_summary(self, task_id: str, results: list[SampleSentimentResult]):
        # 你要做的事：
        # 1. 统计正向 / 中性 / 负向数量
        # 2. 计算三类占比
        # 3. 得到主导情绪
        # 4. 组装成任务级情感摘要

        counter = Counter(item.sentiment_label for item in results)
        total = len(counter)

        positive_count = counter.get(SentimentLabel.positive, 0)
        negative_count = counter.get(SentimentLabel.negative, 0)
        neutral_count = counter.get(SentimentLabel.neutral, 0)

        dominant_sentiment = max(
            SentimentLabel.positive,
            SentimentLabel.negative,
            SentimentLabel.neutral,
            key=lambda label: counter.get(label, 0)
        )

        return TaskSentimentSummary(
            task_id=task_id,
            total_samples=len(results),
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            positive_ratio=round(positive_count / total, 4),
            neutral_ratio=round(neutral_count / total, 4),
            negative_ratio=round(negative_count / total, 4),
            dominant_sentiment=dominant_sentiment,
        )





    def run_sentiment(self, task_id: str, samples: list[NormalizedSample]):
        # 你要做的事：
        # 1. 先生成样本级情感结果
        # 2. 再生成任务级情感摘要
        # 3. 最后组装统一响应
        sample_results = self.build_sample_results(samples)
        task_summary = self.build_task_summary(task_id,results=sample_results)

        return SentimentResponse(
            task_id=task_id,
            summary=task_summary,
            preview_results=sample_results[:5]
        )



sentiment_service = SentimentService()

