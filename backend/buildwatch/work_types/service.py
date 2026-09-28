from typing import Annotated

from fastapi import Depends

from buildwatch.infrastructure.database.manager import DBManager, DBManagerDep
from buildwatch.infrastructure.database.models import WorkTypesORM
from buildwatch.infrastructure.database.specifications import LikeSpec
from buildwatch.infrastructure.database.specifications import LimitOffsetSpec
from buildwatch.shared.exceptions import NotFoundException
from buildwatch.shared.schemas import SearchRequest
from buildwatch.work_types.schemas import WorkTypeResponse
from buildwatch.work_types.specifications import (
    ProjectTypeRequiresSpec,
)


class WorkTypesService:
    """Бизнес-логика типов строительных работ"""

    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    async def get_work_types(self, request: SearchRequest) -> list[WorkTypesORM]:
        """Список типов работ с поиском и пагинацией"""

        offset = max(0, (request.page - 1) * request.page_size)
        return await self.db_manager.work_type_repo.get_work_types(
            LimitOffsetSpec(limit=request.page_size, offset=offset),
            LikeSpec(col=WorkTypesORM.name, value=request.search),
        )

    async def get_work_types_count(self, request: SearchRequest) -> int:
        """Количество типов работ по поисковому запросу"""

        return await self.db_manager.work_type_repo.get_work_types_count(
            LikeSpec(col=WorkTypesORM.name, value=request.search),
        )

    async def get_available_for_project(
        self, project_id: int, request: SearchRequest
    ) -> list[WorkTypeResponse]:
        """Типы работ, доступные для типа указанного проекта"""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")
        offset = max(0, (request.page - 1) * request.page_size)
        work_types = await self.db_manager.work_type_repo.get_work_types(
            ProjectTypeRequiresSpec(project.type_id),
            LikeSpec(col=WorkTypesORM.name, value=request.search),
            LimitOffsetSpec(limit=request.page_size, offset=offset),
        )
        return [WorkTypeResponse.model_validate(wt) for wt in work_types]

    async def get_available_for_project_count(
        self, project_id: int, request: SearchRequest
    ) -> int:
        """Количество доступных типов работ для проекта"""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")
        return await self.db_manager.work_type_repo.get_work_types_count(
            ProjectTypeRequiresSpec(project.type_id),
            LikeSpec(col=WorkTypesORM.name, value=request.search),
        )


def get_work_types_service(
    db_manager: DBManagerDep,
) -> WorkTypesService:
    return WorkTypesService(db_manager)


WorkTypesServiceDep = Annotated[WorkTypesService, Depends(get_work_types_service)]
