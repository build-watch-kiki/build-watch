import logging
from typing import AsyncGenerator, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from buildwatch.settings import get_settings, Settings

logger = logging.getLogger(__name__)


class DatabaseHelper:
    """Управление подключением и сессиями БД"""

    def __init__(self, settings: Settings):
        self.engine = create_async_engine(url=settings.db.POSTGRES_DSN)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def dispose(self) -> None:
        """Завершение работы движка БД"""
        await self.engine.dispose()
        logger.info("Подключение к БД разорвано")

    async def session_getter(self) -> AsyncGenerator[AsyncSession]:
        """Генератор сессий для FastAPI-зависимостей"""
        async with self.session_maker() as session:
            yield session


db_helper = DatabaseHelper(settings=get_settings())

SessionDep = Annotated[AsyncSession, Depends(db_helper.session_getter)]
