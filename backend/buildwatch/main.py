import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from buildwatch.api import router as main_router
from buildwatch.infrastructure.broker import NEW_PHOTO_QUEUE, broker
from buildwatch.infrastructure.database.helper import db_helper
from buildwatch.middleware import ProcessTimeMiddleware
from buildwatch.settings import get_settings
from buildwatch.shared import BuildWatchException

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("build-watch-backend")
except PackageNotFoundError:
    __version__ = "dev"


settings = get_settings()
logging.basicConfig(level=settings.log.level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await broker.start()
    await broker.declare_queue(NEW_PHOTO_QUEUE)
    yield
    await broker.stop()
    await db_helper.dispose()


app = FastAPI(
    title=settings.app.title,
    root_path=settings.run.prefix,
    debug=settings.app.debug,
    lifespan=lifespan,
    version=__version__,
)

app.include_router(main_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeMiddleware)


@app.exception_handler(BuildWatchException)
async def memory_trace_exception_handler(_request: Request, exc: BuildWatchException):
    """Обработчик доменных исключений приложения"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    uvicorn.run(
        "buildwatch.main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.app.debug,
    )
