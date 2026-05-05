from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile

from conf.db_conf import get_db
from crud.dataset_crud import create_dataset, get_dataset_by_id
from crud.task_crud import create_task, get_task_detail

from services.task_service import task_service
from services.topic_service import topic_service
from shcemas.task_schema import CreateTaskRequest, ImportMetadata, TaskDetailResponse, TaskStatus
from crud.dataset_crud import get_dataset_by_id
from crud.task_crud import get_task_detail
from services.preprocess_service import preprocess_service
from services.sentiment_service import sentiment_service
from utils.response import error_response, success_response
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/import")
async def import_task_data(
    file: UploadFile = File(...),
    source_platform: str = Form(...),
    product_line: str | None = Form(default=None),
    date_start: date | None = Form(default=None),
    date_end: date | None = Form(default=None),
    db=Depends(get_db),
):
    metadata = ImportMetadata(
        source_platform=source_platform,
        product_line=product_line,
        date_start=date_start,
        date_end=date_end,
    )
    dataset_payload, response_data = await task_service.build_dataset_import(file=file, metadata=metadata)
    await create_dataset(session=db, payload=dataset_payload)
    await db.commit()
    return success_response(data=response_data.model_dump(), message="dataset imported")


@router.post("")
async def create_task_endpoint(payload: CreateTaskRequest, db=Depends(get_db)):
    dataset = await get_dataset_by_id(session=db, dataset_id=payload.dataset_id)
    if dataset is None:
        return error_response(message="dataset not found", code=1, data=None)

    task_payload, response_data = task_service.build_task_create_payload(dataset=dataset, payload=payload)
    await create_task(session=db, payload=task_payload)
    await db.commit()
    return success_response(data=response_data.model_dump(), message="task created")


@router.get("/{task_id}")
async def get_task_detail_endpoint(task_id: str, db=Depends(get_db)):
    task = await get_task_detail(session=db, task_id=task_id)
    if task is None:
        return error_response(message="task not found", code=1, data=None)

    data = TaskDetailResponse(
        task_id=task.task_id,
        dataset_id=task.dataset_id,
        task_name=task.task_name,
        status=TaskStatus(task.status),
        sample_count=task.sample_count,
        source_platform=task.source_platform,
        product_line=task.product_line,
        created_at=task.created_at,
    )
    return success_response(data=data.model_dump(), message="task detail")




@router.post("/{task_id}/preprocess")
async def preprocess_task(task_id: str, db=Depends(get_db)):
    task = await get_task_detail(session=db, task_id=task_id)
    if task is None:
        return error_response(message="task not found", code=1, data=None)

    dataset = await get_dataset_by_id(session=db, dataset_id=task.dataset_id)
    if dataset is None:
        return error_response(message="dataset not found", code=1, data=None)

    response = preprocess_service.run_preprocess(task_id=task_id, dataset=dataset)
    return success_response(data=response.model_dump(), message="preprocess completed")







@router.post("/{task_id}/sentiment")
async def run_task_sentiment(task_id: str, db=Depends(get_db)):
    task = await get_task_detail(session=db, task_id=task_id)
    if task is None:
        return error_response(message="task not found", code=1, data=None)

    dataset = await get_dataset_by_id(session=db, dataset_id=task.dataset_id)
    if dataset is None:
        return error_response(message="dataset not found", code=1, data=None)

    samples = preprocess_service.get_valid_samples(dataset=dataset)
    response = sentiment_service.run_sentiment(task_id=task_id, samples=samples)
    return success_response(data=response.model_dump(), message="sentiment completed")







@router.post("/{task_id}/topics")
async def run_task_topic_analysis(task_id: str, db=Depends(get_db)):
    task = await get_task_detail(session=db, task_id=task_id)
    if task is None:
        return error_response(message="task not found", code=1, data=None)

    dataset = await get_dataset_by_id(session=db, dataset_id=task.dataset_id)
    if dataset is None:
        return error_response(message="dataset not found", code=1, data=None)

    samples = preprocess_service.get_valid_samples(dataset=dataset)
    sentiment_response = sentiment_service.run_sentiment(task_id=task_id, samples=samples)
    sentiment_map = {
        item.sample_id: item
        for item in sentiment_response.preview_results
    }
    response = topic_service.run_topic_analysis(
        task_id=task_id,
        samples=samples,
        sentiment_map=sentiment_map,
    )
    return success_response(data=response.model_dump(), message="topic analysis completed")