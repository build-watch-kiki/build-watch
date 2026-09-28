from typing import Sequence, Any, Annotated

from fastapi import Depends

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.database.models import WorkTypesORM
from buildwatch.shared.repository import SQLBaseRepository
from buildwatch.work_types.contracts import WorkTypesRepositoryProtocol


class WorkTypesRepository(SQLBaseRepository):
    """Реализация репозитория типов работ"""

    async def get_work_types(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[WorkTypesORM]:
        """Список типов работ"""

        return await self.get_all(WorkTypesORM, *specs, **filter_by)

    async def get_work_types_count(self, *specs: Any, **filter_by: Any) -> int:
        """Количество типов работ"""

        return await self.get_count(WorkTypesORM, *specs, **filter_by)

    async def get_work_type_by_id(
        self, work_type_id: int, *specs: Any
    ) -> WorkTypesORM | None:
        """Тип работ по идентификатору"""

        return await self.get_one(WorkTypesORM, *specs, id=work_type_id)


def get_work_types_repository(session: SessionDep) -> WorkTypesRepositoryProtocol:
    return WorkTypesRepository(session)


WorkTypesRepositoryDep = Annotated[
    WorkTypesRepository, Depends(get_work_types_repository)
]
