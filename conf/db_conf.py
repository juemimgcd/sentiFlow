from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from conf.settings import settings

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 关闭数据库引擎连接池。
async def close_db():
    await engine.dispose()


@asynccontextmanager
# 创建带回滚和关闭逻辑的数据库会话上下文。
async def db_session():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 为接口依赖提供数据库会话。
async def get_db():
    async with db_session() as session:
        yield session
















