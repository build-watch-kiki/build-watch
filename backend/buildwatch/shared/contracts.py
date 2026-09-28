from typing import Any

from infrastructure.database.specifications import Specification


class BaseRepositoryProtocol:
    """Базовый репозиторий для работы с БД"""

    async def get_count(
        self, model, *specs: Specification, **filter_by: Any
    ) -> int: ...

    async def get_all(
        self, model, *specs: Specification, **filter_by: Any
    ) -> list[Any]: ...

    async def get_one(
        self, model, *specs: Specification, **filter_by: Any
    ) -> Any | None: ...
