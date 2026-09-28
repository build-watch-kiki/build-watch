from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from buildwatch.infrastructure.database.models.core.projects import ProjectsORM
from buildwatch.infrastructure.database.specifications.base import Specification


class LoadStages(Specification):
    """Спецификация подгрузки этапов проекта"""

    def apply(self, query: Select) -> Select:
        return query.options(joinedload(ProjectsORM.stages))


class LoadProjectType(Specification):
    """Спецификация подгрузки типа проекта"""

    def apply(self, query: Select) -> Select:
        return query.options(joinedload(ProjectsORM.type))
