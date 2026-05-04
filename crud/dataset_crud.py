from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dataset_model import Dataset
from shcemas.task_schema import CreateDatasetPayload


async def create_dataset(session: AsyncSession, payload: CreateDatasetPayload) -> Dataset:
    dataset = Dataset(**payload.model_dump())
    session.add(dataset)
    await session.flush()
    await session.refresh(dataset)
    return dataset


async def get_dataset_by_id(session: AsyncSession, dataset_id: str) -> Dataset | None:
    stmt = select(Dataset).where(Dataset.dataset_id == dataset_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()



async def update_dataset_preprocess_summary(
        session: AsyncSession,
        dataset_id: str,
        preprocess_status: str,
        valid_sample_count: int,
        invalid_sample_count: int,
        preprocess_summary: str,
) -> Dataset | None:
    pass





