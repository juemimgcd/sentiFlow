import json
from collections import Counter
from datetime import datetime
from uuid import uuid4

from models.dataset_model import Dataset
from shcemas.preprocess_schema import (
    NormalizedSample,
    PreprocessResponse,
    PreprocessSummary,
    RawSample,
)
from utils.text_cleaner import clean_text, is_meaningful_text


class PreprocessService:
    """负责从数据集中加载原始样本并执行文本清洗、标准化和统计汇总。"""

    # 从数据集中加载原始文本样本。
    def load_raw_samples(self, dataset: Dataset) -> list[RawSample]:
        raw_text = (dataset.raw_text or "").strip()
        if not raw_text:
            return []

        rows = []
        for line in raw_text.splitlines():
            content = line.strip()
            if not content:
                continue
            rows.append(RawSample(content=content, extra={}))
        return rows

    # 清洗并标准化单条原始样本。
    def normalize_sample(self, dataset: Dataset, sample: RawSample) -> NormalizedSample:
        cleaned = clean_text(sample.content)
        is_valid = is_meaningful_text(cleaned)
        invalid_reason = None if is_valid else "empty_after_clean"

        return NormalizedSample(
            sample_id=str(uuid4()),
            content_raw=sample.content,
            content_clean=cleaned,
            source_platform=dataset.source_platform,
            published_at=sample.published_at,
            language=None,
            is_valid=is_valid,
            invalid_reason=invalid_reason,
            extra=sample.extra,
        )

    # 汇总预处理后的有效和无效样本统计。
    def build_summary(self, normalized_samples: list[NormalizedSample]) -> PreprocessSummary:
        valid_samples = [item for item in normalized_samples if item.is_valid]
        invalid_samples = [item for item in normalized_samples if not item.is_valid]

        counter = Counter(
            item.invalid_reason for item in invalid_samples if item.invalid_reason
        )

        return PreprocessSummary(
            raw_sample_count=len(normalized_samples),
            valid_sample_count=len(valid_samples),
            invalid_sample_count=len(invalid_samples),
            invalid_reason_stats=dict(counter),
            preview_samples=valid_samples[:3],
            processed_at=datetime.utcnow(),
        )

    # 获取清洗标准化后的有效样本，供情感分析和主题分析复用。
    def get_valid_samples(self, dataset: Dataset) -> list[NormalizedSample]:
        raw_samples = self.load_raw_samples(dataset)
        normalized_samples = [
            self.normalize_sample(dataset=dataset, sample=sample)
            for sample in raw_samples
        ]
        return [sample for sample in normalized_samples if sample.is_valid]

    # 执行任务对应数据集的完整预处理流程。
    def run_preprocess(self, task_id: str, dataset: Dataset) -> PreprocessResponse:
        raw_samples = self.load_raw_samples(dataset)
        normalized_samples = [
            self.normalize_sample(dataset=dataset, sample=sample)
            for sample in raw_samples
        ]
        summary = self.build_summary(normalized_samples)
        return PreprocessResponse(
            task_id=task_id,
            dataset_id=dataset.dataset_id,
            summary=summary,
        )


preprocess_service = PreprocessService()
