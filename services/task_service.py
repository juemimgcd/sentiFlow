import csv
import json
from datetime import datetime
from io import StringIO
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from shcemas.task_schema import (
    CreateTaskRequest,
    CreateTaskResponse,
    ImportDatasetResponse,
    ImportMetadata,
    TaskDetailResponse,
    TaskStatus,
)

_DATASET_STORE: dict[str, dict] = {}
_TASK_STORE: dict[str, dict] = {}
SUPPORTED_IMPORT_TYPES = {"csv", "json", "pdf", "docx", "pptx", "xlsx", "html"}



class TaskService:
    async def import_dataset(
            self,
            file: UploadFile,
            metadata: ImportMetadata,
    ) -> ImportDatasetResponse:
        if file.filename:
            suffix = file.filename.split(".")[1]
            if suffix not in SUPPORTED_IMPORT_TYPES:
                raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="wrong file type")

            file_bytes = file.read()




































