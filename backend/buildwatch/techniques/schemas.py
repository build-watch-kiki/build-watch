from datetime import datetime

from pydantic import Field, BaseModel, ConfigDict

from buildwatch.shared.schemas import AppBaseModel


class TechniqueBase(AppBaseModel):
    """Базовая Pydantic-модель строительной техники"""

    name: str
    name_ru: str = Field(alias="nameRu")
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TechniqueCreate(AppBaseModel):
    """Схема для создания техники"""

    name: str
    name_ru: str = Field(alias="nameRu")
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TechniqueUpdate(AppBaseModel):
    """Схема для обновления техники"""

    name: str | None = Field(default=None, max_length=127)
    name_ru: str | None = Field(default=None, max_length=127, alias="nameRu")
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TechniqueResponse(TechniqueBase):
    """Схема ответа для техники"""

    id: int
    created_at: datetime
