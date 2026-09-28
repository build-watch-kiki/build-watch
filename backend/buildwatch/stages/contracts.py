from typing import Protocol, Sequence, Any

from buildwatch.infrastructure.database.models import StagesORM


class StagesRepositoryProtocol(Protocol):
    """Контракт репозитория этапов"""

    async def create_stage(
        self,
        project_id: int,
        parent_id: int | None,
        work_type_id: int,
        name: str,
        start_dt: Any,
        end_dt: Any,
    ) -> int: ...

    async def get_stages(
        self, *specs: Any, **filter_by: Any
    ) -> Sequence[StagesORM]: ...

    async def get_stage_by_id(self, stage_id: int, *specs: Any) -> StagesORM | None: ...

    async def update_stage(self, stage_id: int, **kwargs: Any) -> None: ...

    async def delete_stage(self, stage_id: int) -> None: ...

    async def get_count(self, model: Any, *specs: Any, **filter_by: Any) -> int: ...

    async def set_stage_techniques(
        self, stage_id: int, techniques: list[tuple[int, int]]
    ) -> None: ...
