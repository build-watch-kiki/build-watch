from typing import Protocol, Sequence, Any

from buildwatch.infrastructure.database.models import WorkTypesORM


class WorkTypesRepositoryProtocol(Protocol):

    async def get_work_types(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[WorkTypesORM]: ...

    async def get_work_types_count(self, *specs: Any, **filter_by: Any) -> int: ...
