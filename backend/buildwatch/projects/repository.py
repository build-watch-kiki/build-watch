import logging
from typing import Sequence, Any, Annotated

from fastapi import Depends
from sqlalchemy import select

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.database.models import ProjectTypesORM
from buildwatch.infrastructure.database.models.core.projects import ProjectsORM
from buildwatch.projects.contracts import ProjectsRepositoryProtocol
from buildwatch.shared.repository import SQLBaseRepository

logger = logging.getLogger(__name__)


class ProjectsRepository(SQLBaseRepository, ProjectsRepositoryProtocol):
    """Реализация репозитория проектов"""

    async def create_project(
        self, name: str, type_id: int, start_dt: Any, end_dt: Any
    ) -> int:
        """Создание проекта"""

        logger.debug("Creating project: %s", name)
        project = ProjectsORM(
            name=name, type_id=type_id, start_dt=start_dt, end_dt=end_dt
        )
        self.session.add(project)
        await self.session.flush()
        logger.debug("Project created with id: %d", project.id)
        return project.id

    async def delete_project(
        self, project_id: int, *specs: Any
    ) -> None:
        logger.debug("Deleting project: %d", project_id)
        stage = await self.get_one(ProjectsORM, id=project_id)
        if stage is None:
            return
        await self.session.delete(stage)
        await self.session.flush()

    async def get_projects(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[ProjectsORM]:
        """Список проектов по фильтрам и спецификациям"""

        logger.debug("Getting projects with filter: %s", filter_by)
        return await self.get_all(ProjectsORM, *specs, **filter_by)

    async def get_project_types(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[ProjectTypesORM]:
        """Список типов проектов"""

        logger.debug("Getting project types with filter: %s", filter_by)
        return await self.get_all(ProjectTypesORM, *specs, **filter_by)

    async def get_project_types_count(self, *specs: Any, **filter_by: Any) -> int:
        """Количество типов проектов по фильтрам"""

        return await self.get_count(ProjectTypesORM, *specs, **filter_by)

    async def get_project_by_id(
        self, project_id: int, *specs: Any
    ) -> ProjectsORM | None:
        """Проект по идентификатору"""

        logger.debug("Getting project by id: %d", project_id)
        return await self.get_one(ProjectsORM, *specs, id=project_id)

    async def update_project(self, project_id: int, **kwargs: Any) -> None:
        """Обновление полей проекта"""

        logger.debug("Updating project: %d", project_id)
        project = await self.get_one(ProjectsORM, id=project_id)
        if project is None:
            return
        for key, value in kwargs.items():
            setattr(project, key, value)
        await self.session.flush()


def get_project_repository(session: SessionDep) -> ProjectsRepositoryProtocol:
    return ProjectsRepository(session)


ProjectsRepositoryDep = Annotated[ProjectsRepository, Depends(get_project_repository)]
