from typing import Annotated

from fastapi import Depends

from buildwatch.infrastructure.database.manager import DBManager, DBManagerDep
from buildwatch.infrastructure.database.models import ProjectTypesORM, ProjectsORM
from buildwatch.infrastructure.database.specifications import LikeSpec
from buildwatch.projects.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectTypeResponse,
    ProjectUpdate,
)
from buildwatch.shared.exceptions import NotFoundException
from buildwatch.shared.schemas import PaginationSchema
from buildwatch.infrastructure.database.specifications import LimitOffsetSpec
from buildwatch.shared.schemas import SearchRequest


class ProjectService:
    """Бизнес-логика проектов и типов проектов"""

    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    async def get_projects_count(self) -> int:
        """Общее количество проектов"""

        return await self.db_manager.project_repo.get_count(ProjectsORM)

    async def get_projects(self, pagination: PaginationSchema) -> list[ProjectResponse]:
        """Список проектов для пагинации"""

        offset = max(0, (pagination.page - 1) * pagination.page_size)
        projects = await self.db_manager.project_repo.get_projects(
            LimitOffsetSpec(limit=pagination.page_size, offset=offset),
        )
        return [ProjectResponse.model_validate(project) for project in projects]

    async def get_project(self, project_id: int) -> ProjectResponse:
        """Проект по идентификатору"""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")
        return ProjectResponse.model_validate(project)

    async def create_project(self, payload: ProjectCreate) -> int:
        """Создание проекта по имени типа"""

        project_types = await self.db_manager.project_repo.get_project_types(
            name=payload.type_name,
        )
        if not project_types:
            raise NotFoundException(
                f"Тип проекта с названием: '{payload.type_name}' не найден"
            )

        project_id = await self.db_manager.project_repo.create_project(
            name=payload.name,
            end_dt=payload.end_dt,
            start_dt=payload.start_dt,
            type_id=project_types[0].id,
        )
        await self.db_manager.commit()
        return project_id

    async def delete_project(self, project_id: int) -> None:
        """Создание проекта по имени типа"""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")

        await self.db_manager.project_repo.delete_project(
            project_id=project_id,
        )
        await self.db_manager.commit()
        return None


    async def get_project_types(
        self, request: SearchRequest
    ) -> list[ProjectTypeResponse]:
        """Список типов проектов с поиском"""

        offset = max(0, (request.page - 1) * request.page_size)
        project_types = await self.db_manager.project_repo.get_project_types(
            LikeSpec(col=ProjectTypesORM.name, value=request.search),
            LimitOffsetSpec(limit=request.page_size, offset=offset),
        )
        return [
            ProjectTypeResponse.model_validate(project_type)
            for project_type in project_types
        ]

    async def get_project_types_count(self, request: SearchRequest) -> int:
        """Количество типов проектов по поисковому запросу"""

        return await self.db_manager.project_repo.get_project_types_count(
            LikeSpec(col=ProjectTypesORM.name, value=request.search),
        )

    async def update_project(
        self, project_id: int, payload: ProjectUpdate
    ) -> ProjectResponse:
        """Обновление проекта по идентификатору"""

        project = await self.db_manager.project_repo.get_project_by_id(project_id)
        if project is None:
            raise NotFoundException(f"Проект с id {project_id} не найден")

        update_data = payload.model_dump(exclude_unset=True)
        if payload.type_id is not None:
            project_type = await self.db_manager.project_repo.get_project_types(
                id=payload.type_id
            )
            if not project_type:
                raise NotFoundException(
                    f"Тип проекта с id {payload.type_id} не найден"
                )
        await self.db_manager.project_repo.update_project(project_id, **update_data)
        await self.db_manager.commit()
        return ProjectResponse.model_validate(
            await self.db_manager.project_repo.get_project_by_id(
                project_id
            )
        )

def get_project_service(db_manager: DBManagerDep):
    return ProjectService(db_manager)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
