from collections import Counter
from typing import Any

from conf.settings import settings
from shcemas.preprocess_schema import NormalizedSample, PreprocessResponse
from shcemas.sentiment_schema import (
    SampleSentimentResult,
    SentimentLabel,
    SentimentResponse,
    TaskSentimentSummary,
)


class SentimentService:
    """负责调用情感模型并汇总样本级、任务级情感分析结果。"""

    def __init__(self) -> None:
        # 延迟加载模型，避免应用启动时立刻触发 Hugging Face 下载。
        self.classifier: Any | None = None

    # 判断单条标准化样本的情感标签和置信分。
    def classify_sample(self, sample: NormalizedSample) -> tuple[SentimentLabel, float, str]:
        text = sample.content_clean.strip()
        if not text:
            return SentimentLabel.neutral, 0.0, "空文本，默认中性"

        result = self._get_classifier()(text)[0]
        raw_label = str(result["label"])
        score = float(result["score"])

        if score < settings.SENTIMENT_NEUTRAL_THRESHOLD:
            return SentimentLabel.neutral, score, "模型置信度较低，归为中性"

        label = self._map_model_label(raw_label)
        return label, score, f"{settings.SENTIMENT_MODEL_NAME} 模型预测"

    # 获取 Hugging Face 情感分类模型。
    def _get_classifier(self):
        if self.classifier is None:
            try:
                from transformers import pipeline
            except ImportError as exc:
                raise RuntimeError(
                    "缺少 transformers/torch 依赖，请先安装项目依赖后再运行情感分析"
                ) from exc

            self.classifier = pipeline(
                "text-classification",
                model=settings.SENTIMENT_MODEL_NAME,
            )
        return self.classifier

    # 将模型原始标签映射为项目内部情感标签。
    @staticmethod
    def _map_model_label(raw_label: str) -> SentimentLabel:
        label = raw_label.lower()
        if label in {"positive", "pos", "label_1", "1"}:
            return SentimentLabel.positive
        if label in {"negative", "neg", "label_0", "0"}:
            return SentimentLabel.negative
        return SentimentLabel.neutral

    # 生成所有样本的情感分析结果列表。
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

    # 汇总任务级情感统计结果。
    def build_task_summary(self, task_id: str, results: list[SampleSentimentResult]):
        # 你要做的事：
        # 1. 统计正向 / 中性 / 负向数量
        # 2. 计算三类占比
        # 3. 得到主导情绪
        # 4. 组装成任务级情感摘要

        counter = Counter(item.sentiment_label for item in results)
        total = len(results)
        if total == 0:
            return TaskSentimentSummary(
                task_id=task_id,
                total_samples=0,
                positive_count=0,
                neutral_count=0,
                negative_count=0,
                positive_ratio=0.0,
                neutral_ratio=0.0,
                negative_ratio=0.0,
                dominant_sentiment=SentimentLabel.neutral,
            )

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





    # 运行情感分析并组装统一响应。
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

