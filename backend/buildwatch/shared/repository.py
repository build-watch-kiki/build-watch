from typing import Any

from sqlalchemy import Select, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from buildwatch.infrastructure.database.specifications.base import Specification


class SQLBaseRepository:
    """Базовый репозиторий для работы с БД"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def apply_specs(self, query: Select, *specs: Specification) -> Select:
        """Применение спецификаций к запросу"""

        for spec in specs:
            query = spec.apply(query)
        return query

    async def get_count(self, model, *specs: Specification, **filter_by: Any) -> int:
        """Количество записей по фильтрам и спецификациям"""

        query = select(func.count()).select_from(model).filter_by(**filter_by)
        query = self.apply_specs(query, *specs)
        res = await self.session.execute(query)
        return res.scalar_one()

    async def get_all(
        self, model, *specs: Specification, **filter_by: Any
    ) -> list[Any]:
        """Список записей по фильтрам и спецификациям"""

        query = select(model).filter_by(**filter_by)
        query = self.apply_specs(query, *specs)
        res = await self.session.execute(query)
        return list(res.unique().scalars().all())

    async def get_one(
        self, model, *specs: Specification, **filter_by: Any
    ) -> Any | None:
        """Одна запись по фильтрам или None"""

        query = select(model).filter_by(**filter_by)
        query = self.apply_specs(query, *specs)
        res = await self.session.execute(query)
        return res.unique().scalar_one_or_none()
