from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from shcemas.task_schema import TaskStatus


class AnalysisTaskType(str, Enum):
    full_analysis = "full_analysis"


class AnalysisTaskMessage(BaseModel):
    task_id: str
    dataset_id: str
    task_type: AnalysisTaskType = AnalysisTaskType.full_analysis
    requested_at: datetime
    trace_id: str


class EnqueueTaskResponse(BaseModel):
    task_id: str
    dataset_id: str
    status: TaskStatus
    queue_name: str
    enqueued: bool