from typing import Protocol, Sequence, Any

from buildwatch.infrastructure.database.models import ProjectTypesORM
from buildwatch.infrastructure.database.models.core.projects import ProjectsORM


class ProjectsRepositoryProtocol(Protocol):
    """Контракт репозитория проектов"""

    async def create_project(
        self, name: str, type_id: int, start_dt: Any, end_dt: Any
    ) -> int: ...

    async def delete_project(
        self, project_id: int, *specs: Any
    ) -> None: ...

    async def get_projects(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[ProjectsORM]: ...

    async def get_project_types(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[ProjectTypesORM]: ...

    async def get_project_by_id(
        self, project_id: int, *specs: Any
    ) -> ProjectsORM | None: ...

    async def update_project(self, project_id: int, **kwargs: Any) -> None: ...