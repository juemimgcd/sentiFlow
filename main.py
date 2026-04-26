from contextlib import asynccontextmanager

from fastapi import FastAPI

from conf.db_conf import close_db, engine
from conf.logging import app_logger, setup_logger
from conf.settings import settings
from models.base import Base
from models import Dataset, Task
from router.health import router as health_router
from router.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logger()
    app_logger.bind(module="system").info("application starts")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
    finally:
        app_logger.bind(module="system").info("application ends")
        logger_complete = app_logger.complete()
        if logger_complete:
            await logger_complete
        await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.APP_DEBUG,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    app.include_router(health_router, prefix=settings.APP_API_PREFIX)
    app.include_router(tasks_router, prefix=settings.APP_API_PREFIX)
    return app


app = create_app()
