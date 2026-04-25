from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/import")
async def import_task_data():
    raise NotImplementedError


@router.post("")
async def create_task():
    raise NotImplementedError


@router.get("/{task_id}")
async def get_task_detail(task_id: str):
    raise NotImplementedError