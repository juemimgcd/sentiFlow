from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task_model import Task
from shcemas.task_schema import CreateTaskPayload, TaskStatus


# 新建分析任务记录并刷新数据库状态。
async def create_task(session: AsyncSession, payload: CreateTaskPayload) -> Task:
    task = Task(**payload.model_dump(mode="python"))
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


# 根据任务 ID 查询任务详情。
async def get_task_detail(session: AsyncSession, task_id: str) -> Task | None:
    stmt = select(Task).where(Task.task_id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()



async def update_task_status(
    session: AsyncSession,
    task_id: str,
    status: TaskStatus,
) -> Task | None:
    task = await get_task_detail(session=session, task_id=task_id)
    if task is None:
        return None

    task.status = status.value
    await session.flush()
    await session.refresh(task)
    return task