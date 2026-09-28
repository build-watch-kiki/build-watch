from datetime import datetime
from pydantic import Field, ConfigDict
from buildwatch.shared.schemas import AppBaseModel


class WorkTypeBase(AppBaseModel):
    """Базовая Pydantic-модель типа строительных работ"""

    name: str
    # code: str | None = None
    # parent_id: int | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WorkTypeCreate(WorkTypeBase):
    """Схема для создания типа работ"""

    pass


class WorkTypeUpdate(AppBaseModel):
    """Схема для обновления типа работ"""

    name: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=31)
    parent_id: int | None = None


class WorkTypeResponse(WorkTypeBase):
    """Схема ответа для типа работ"""

    id: int
    created_at: datetime
