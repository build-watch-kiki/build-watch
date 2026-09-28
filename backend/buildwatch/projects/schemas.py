from datetime import datetime

from pydantic import Field, ConfigDict

from buildwatch.shared.schemas import (
    AppBaseModel,
    DeadlinesSchema,
    OptionalDeadlinesSchema,
)


class ProjectTypeBase(AppBaseModel):
    """Базовая Pydantic-модель типа проекта"""

    name: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectTypeCreate(ProjectTypeBase):
    """Схема для создания типа проекта"""

    pass


class ProjectTypeUpdate(AppBaseModel):
    """Схема для обновления типа проекта"""

    name: str | None = Field(default=None, max_length=31)


class ProjectBase(DeadlinesSchema):
    """Базовая Pydantic-модель проекта"""

    name: str
    type_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectCreate(DeadlinesSchema):
    """Схема для создания проекта"""

    name: str
    type_name: str = Field(examples=["Дороги", "Школа", "ДОУ"], alias="type")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectUpdate(OptionalDeadlinesSchema):
    """Схема для обновления проекта"""

    name: str | None = Field(default=None, max_length=63)
    type_id: int | None = None


class ProjectTypeResponse(ProjectTypeBase):
    """Схема ответа для типа проекта"""

    id: int
    created_at: datetime


class ProjectResponse(DeadlinesSchema):
    """Схема ответа для проекта со связанными типами"""

    id: int
    name: str
    created_at: datetime
    type: ProjectTypeResponse = Field(serialization_alias="projectType")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
