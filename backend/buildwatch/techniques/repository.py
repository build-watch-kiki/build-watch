import logging
from typing import Sequence, Any, Annotated

from fastapi import Depends

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.database.models.core.techniques import TechniquesORM
from buildwatch.settings import get_settings
from buildwatch.shared.repository import SQLBaseRepository
from buildwatch.techniques.contracts import TechniqueRepositoryProtocol
from buildwatch.techniques.mock import MockTechniqueRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class TechniquesRepository(SQLBaseRepository, TechniqueRepositoryProtocol):
    """Реализация репозитория техники"""

    async def create_technique(self, name: str, name_ru: str, color: str) -> int:
        """Создание техники"""
        logger.debug("Creating technique: %s", name)
        technique = TechniquesORM(name=name, name_ru=name_ru, color=color)
        self.session.add(technique)
        await self.session.flush()
        return technique.id

    async def get_techniques(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[TechniquesORM]:
        """Список техники"""
        return await self.get_all(TechniquesORM, *specs, **filter_by)

    async def get_technique_by_id(
        self, technique_id: int, *specs: Any
    ) -> TechniquesORM | None:
        """Техника по ID"""
        return await self.get_one(TechniquesORM, *specs, id=technique_id)

    async def update_technique(self, technique_id: int, **kwargs: Any) -> None:
        """Обновление техники"""
        technique = await self.get_one(TechniquesORM, id=technique_id)
        if technique:
            for k, v in kwargs.items():
                setattr(technique, k, v)
            await self.session.flush()

    async def delete_technique(self, technique_id: int) -> None:
        """Удаление техники"""
        technique = await self.get_one(TechniquesORM, id=technique_id)
        if technique:
            await self.session.delete(technique)
            await self.session.flush()


def get_technique_repository(session: SessionDep) -> TechniqueRepositoryProtocol:
    if settings.use_mock.technique_repo:
        return MockTechniqueRepository()
    return TechniquesRepository(session)


TechniquesRepositoryDep = Annotated[
    TechniquesRepository, Depends(get_technique_repository)
]
