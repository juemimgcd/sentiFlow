from contextlib import asynccontextmanager

from fastapi import FastAPI

from conf.db_conf import close_db
from conf.logging import app_logger, setup_logger
from conf.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logger()
    app_logger.bind(module="system").info("application starts")
    try:
        yield
    finally:
        app_logger.bind(module="system").info("application ends")
        logger_complete = app_logger.complete()
        if logger_complete:
            await logger_complete
        await close_db()

def create_app() -> FastAPI:
    return FastAPI(
        title=settings.APP_NAME,
        debug=settings.APP_DEBUG,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )


app = create_app()


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
