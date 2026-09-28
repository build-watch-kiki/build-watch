from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from buildwatch.infrastructure.database.models.core.projects import WorkTypesORM
from buildwatch.infrastructure.database.models.core.stages import StagesORM
from buildwatch.infrastructure.database.models.core.techniques import StageTechniquesORM
from buildwatch.infrastructure.database.specifications.base import Specification


class LoadChildren(Specification):
    """Спецификация подгрузки дочерних этапов"""

    def apply(self, query: Select) -> Select:
        return query.options(joinedload(StagesORM.children))


class LoadWorkType(Specification):
    """Спецификация подгрузки типа работ"""

    def apply(self, query: Select) -> Select:
        return query.options(joinedload(StagesORM.work_type))


class LoadProject(Specification):
    """Спецификация подгрузки проекта"""

    def apply(self, query: Select) -> Select:
        return query.options(joinedload(StagesORM.project))


class LoadTechniques(Specification):
    """Спецификация подгрузки техник"""

    def apply(self, query: Select) -> Select:
        return query.options(
            joinedload(StagesORM.technique_links).joinedload(
                StageTechniquesORM.technique
            )
        )


class StageWorkTypeNameSpec(Specification):
    """Поиск этапов по имени типа работ, которое видно в API."""

    def __init__(self, value: str | None):
        self.value = value

    def apply(self, query: Select) -> Select:
        if not self.value:
            return query
        return query.where(
            StagesORM.work_type.has(WorkTypesORM.name.ilike(f"%{self.value}%"))
        )
