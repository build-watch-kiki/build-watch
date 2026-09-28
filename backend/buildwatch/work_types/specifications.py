from sqlalchemy import Select

from buildwatch.infrastructure.database.models import WorkTypesORM
from buildwatch.infrastructure.database.specifications.base import Specification


class ProjectTypeRequiresSpec(Specification):
    """Фильтрация через association_proxy: WHERE work_types.id IN (...)"""

    def __init__(self, project_type_id: int):
        self.project_type_id = project_type_id

    def apply(self, query: Select) -> Select:
        return query.where(WorkTypesORM.project_types.any(id=self.project_type_id))
