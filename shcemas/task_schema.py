from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"


class ImportMetadata(BaseModel):
    source_platform: str = Field(..., description="来源平台")
    product_line: str | None = Field(default=None, description="产品线")
    date_start: date | None = Field(default=None, description="起始日期")
    date_end: date | None = Field(default=None, description="结束日期")


class ImportDatasetResponse(BaseModel):
    dataset_id: str
    file_name: str
    file_type: str
    extraction_mode: str
    sample_count: int
    preview_texts: list[str] = Field(default_factory=list)
    metadata: ImportMetadata


class CreateTaskRequest(BaseModel):
    dataset_id: str
    task_name: str = Field(..., min_length=1, description="任务名称")


class CreateDatasetPayload(BaseModel):
    dataset_id: str
    file_name: str
    file_type: str
    extraction_mode: str
    source_platform: str
    product_line: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    sample_count: int
    raw_text: str | None = None


class CreateTaskPayload(CreateTaskRequest):
    task_id: str
    status: TaskStatus
    sample_count: int
    source_platform: str
    product_line: str | None = None
    created_at: datetime


class CreateTaskResponse(BaseModel):
    task_id: str
    dataset_id: str
    status: TaskStatus
    created_at: datetime


class TaskDetailResponse(BaseModel):
    task_id: str
    dataset_id: str
    task_name: str
    status: TaskStatus
    sample_count: int
    source_platform: str
    product_line: str | None = None
    created_at: datetime
