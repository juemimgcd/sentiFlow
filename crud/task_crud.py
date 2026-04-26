from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task_model import Task
from shcemas.task_schema import CreateTaskPayload


async def create_task(session: AsyncSession, payload: CreateTaskPayload) -> Task:
    task = Task(**payload.model_dump(mode="python"))
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


async def get_task_detail(session: AsyncSession, task_id: str) -> Task | None:
    stmt = select(Task).where(Task.task_id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
