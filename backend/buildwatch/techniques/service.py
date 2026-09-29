from typing import Annotated
from fastapi import Depends

from buildwatch.infrastructure.database.manager import DBManager, DBManagerDep
from buildwatch.infrastructure.database.models import TechniquesORM
from buildwatch.infrastructure.database.specifications import LimitOffsetSpec, OrLikeSpec
from buildwatch.shared.exceptions import NotFoundException
from buildwatch.shared.schemas import SearchRequest
from buildwatch.techniques.colors import resolve_color, validate_hex_color
from buildwatch.techniques.schemas import (
    TechniqueResponse,
    TechniqueCreate,
    TechniqueUpdate,
)


class TechniqueService:
    """Бизнес-логика техники"""

    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    async def get_techniques(self, request: SearchRequest) -> list[TechniqueResponse]:
        """Список доступной техники"""
        offset = max(0, (request.page - 1) * request.page_size)
        techniques = await self.db_manager.technique_repo.get_techniques(
            LimitOffsetSpec(limit=request.page_size, offset=offset),
            OrLikeSpec(
                cols=(TechniquesORM.name, TechniquesORM.name_ru),
                value=request.search,
            ),
        )
        return [TechniqueResponse.model_validate(t) for t in techniques]

    async def get_techniques_count(self, request: SearchRequest) -> int:
        """Количество техники"""
        return await self.db_manager.technique_repo.get_count(
            TechniquesORM,
            OrLikeSpec(
                cols=(TechniquesORM.name, TechniquesORM.name_ru),
                value=request.search,
            ),
        )

    async def create_technique(self, payload: TechniqueCreate) -> int:
        """Создание техники"""
        color = resolve_color(payload.name_ru, payload.name, payload.color)
        tid = await self.db_manager.technique_repo.create_technique(
            name=payload.name, name_ru=payload.name_ru, color=color
        )
        await self.db_manager.commit()
        return tid

    async def get_technique_by_id(self, technique_id: int) -> TechniqueResponse:
        """Техника по идентификатору"""
        technique = await self.db_manager.technique_repo.get_technique_by_id(
            technique_id
        )
        if technique is None:
            raise NotFoundException(f"Техника с id {technique_id} не найдена")
        return TechniqueResponse.model_validate(technique)

    async def update_technique(
        self, technique_id: int, payload: TechniqueUpdate
    ) -> TechniqueResponse:
        """Обновление техники"""
        data = payload.model_dump(exclude_unset=True)
        if data.get("color") is not None:
            data["color"] = validate_hex_color(data["color"])
        await self.db_manager.technique_repo.update_technique(
            technique_id, **data
        )
        await self.db_manager.commit()
        return await self.get_technique_by_id(technique_id)

    async def delete_technique(self, technique_id: int) -> None:
        """Удаление техники"""
        await self.db_manager.technique_repo.delete_technique(technique_id)
        await self.db_manager.commit()


def get_technique_service(db_manager: DBManagerDep) -> TechniqueService:
    return TechniqueService(db_manager)


TechniqueServiceDep = Annotated[TechniqueService, Depends(get_technique_service)]
