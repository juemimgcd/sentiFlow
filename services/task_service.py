import csv
import json
from datetime import datetime
from io import BytesIO, StringIO
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from models.dataset_model import Dataset
from shcemas.task_schema import (
    CreateDatasetPayload,
    CreateTaskRequest,
    CreateTaskPayload,
    CreateTaskResponse,
    ImportDatasetResponse,
    ImportMetadata,
    TaskStatus,
)

NATIVE_IMPORT_TYPES = {"csv", "json"}


class TaskService:
    """负责数据集导入解析和分析任务创建所需的载荷组装。"""

    # 解析上传文件并构建数据集导入载荷。
    async def build_dataset_import(
        self,
        file: UploadFile,
        metadata: ImportMetadata,
    ) -> tuple[CreateDatasetPayload, ImportDatasetResponse]:
        suffix = self._extract_suffix(file.filename)
        file_bytes = await file.read()
        rows, extraction_mode = self._extract_rows(file_bytes=file_bytes, file_type=suffix)
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="empty dataset is not allowed",
            )

        dataset_id = str(uuid4())
        dataset_payload = CreateDatasetPayload(
            dataset_id=dataset_id,
            file_name=file.filename or "unknown",
            file_type=suffix,
            extraction_mode=extraction_mode,
            source_platform=metadata.source_platform,
            product_line=metadata.product_line,
            date_start=metadata.date_start,
            date_end=metadata.date_end,
            sample_count=len(rows),
            raw_text="\n".join(item["content"] for item in rows),
        )

        preview_texts = [item["content"] for item in rows[:3]]
        response = ImportDatasetResponse(
            dataset_id=dataset_id,
            file_name=file.filename or "unknown",
            file_type=suffix,
            extraction_mode=extraction_mode,
            sample_count=len(rows),
            preview_texts=preview_texts,
            metadata=metadata,
        )
        return dataset_payload, response

    # 构建新建分析任务所需的数据库载荷和响应。
    def build_task_create_payload(
        self,
        dataset: Dataset,
        payload: CreateTaskRequest,
    ) -> tuple[CreateTaskPayload, CreateTaskResponse]:
        task_id = str(uuid4())
        now = datetime.utcnow()
        task_payload = CreateTaskPayload(
            task_id=task_id,
            dataset_id=payload.dataset_id,
            task_name=payload.task_name,
            status=TaskStatus.pending,
            sample_count=dataset.sample_count,
            source_platform=dataset.source_platform,
            product_line=dataset.product_line,
            created_at=now,
        )
        response = CreateTaskResponse(
            task_id=task_id,
            dataset_id=payload.dataset_id,
            status=TaskStatus.pending,
            created_at=now,
        )
        return task_payload, response

    @staticmethod
    # 从文件名中提取小写后缀。
    def _extract_suffix(filename: str | None) -> str:
        if not filename or "." not in filename:
            return "bin"
        return filename.rsplit(".", 1)[-1].lower()

    # 根据文件类型选择对应解析器提取数据行。
    def _extract_rows(self, file_bytes: bytes, file_type: str) -> tuple[list[dict], str]:
        if file_type == "csv":
            return self._parse_csv(file_bytes.decode("utf-8")), "csv_adapter"
        if file_type == "json":
            return self._parse_json(file_bytes.decode("utf-8")), "json_adapter"
        return self._parse_with_markitdown(file_bytes=file_bytes, file_type=file_type)

    @staticmethod
    # 解析 CSV 文本中的有效内容行。
    def _parse_csv(raw_text: str) -> list[dict]:
        reader = csv.DictReader(StringIO(raw_text))
        rows: list[dict] = []
        for item in reader:
            content = (item.get("content") or "").strip()
            if not content:
                continue
            rows.append(
                {
                    "content": content,
                    "published_at": item.get("published_at"),
                    "extra": item,
                }
            )
        return rows

    @staticmethod
    # 解析 JSON 文本中的有效内容行。
    def _parse_json(raw_text: str) -> list[dict]:
        payload = json.loads(raw_text)
        if not isinstance(payload, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="json payload must be a list",
            )

        rows: list[dict] = []
        for item in payload:
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            rows.append(
                {
                    "content": content,
                    "published_at": item.get("published_at"),
                    "extra": item,
                }
            )
        return rows

    @staticmethod
    # 使用 MarkItDown 解析复杂文档类型。
    def _parse_with_markitdown(file_bytes: bytes, file_type: str) -> tuple[list[dict], str]:
        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"markitdown support is not installed for .{file_type} files",
            ) from exc

        stream = BytesIO(file_bytes)
        stream.name = f"upload.{file_type}"

        converter = MarkItDown(enable_plugins=False)
        try:
            result = converter.convert_stream(stream)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"markitdown failed to parse .{file_type} file",
            ) from exc
        markdown_text = (result.text_content or "").strip()
        if not markdown_text:
            return [], "markitdown_adapter"

        rows = [
            {
                "content": markdown_text,
                "published_at": None,
                "extra": {"file_type": file_type, "byte_size": len(file_bytes)},
            }
        ]
        return rows, "markitdown_adapter"


task_service = TaskService()
