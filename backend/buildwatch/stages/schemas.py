from datetime import datetime

from pydantic import AliasPath, Field, ConfigDict, model_validator

from buildwatch.shared.schemas import (
    AppBaseModel,
    DeadlinesSchema,
    OptionalDeadlinesSchema,
)
from buildwatch.progress.schemas import StageActualProgressResponse
from buildwatch.techniques.schemas import TechniqueResponse


class StageBase(DeadlinesSchema):
    """Базовая Pydantic-модель этапа строительства"""

    project_id: int
    parent_id: int | None = None
    work_type_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StageTechniqueRequest(AppBaseModel):
    name: str
    quantity: int = Field(ge=1, strict=True)
    model_config = ConfigDict(extra="forbid")


class StageTechniqueResponse(TechniqueResponse):
    quantity: int

    @model_validator(mode="before")
    @classmethod
    def from_link(cls, value):
        if hasattr(value, "technique") and hasattr(value, "quantity"):
            technique = TechniqueResponse.model_validate(value.technique)
            return {**technique.model_dump(), "quantity": value.quantity}
        return value


class StageCreate(DeadlinesSchema):
    """Схема для создания этапа — project_id берется из пути."""

    parent_id: int | None = None
    work_type_id: int
    techniques: list[StageTechniqueRequest] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, extra="forbid"
    )


class StageUpdate(OptionalDeadlinesSchema):
    """Схема для обновления этапа"""

    parent_id: int | None = None
    work_type_id: int | None = None

    model_config = ConfigDict(extra="forbid")


class StageResponse(DeadlinesSchema):
    """Схема ответа для этапа — плоский вид для диаграммы Ганта"""

    id: int
    parent_id: int | None = None
    created_at: datetime
    work_type_id: int
    work_type_name: str = Field(
        validation_alias=AliasPath("work_type", "name"),
        serialization_alias="workTypeName",
    )
    techniques: list[StageTechniqueResponse] = Field(
        default_factory=list,
        validation_alias="technique_links",
        serialization_alias="requiresTechnique",
    )
    actual: StageActualProgressResponse | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StageTechniquesBindRequest(AppBaseModel):
    """Полная замена набора техники этапа."""

    techniques: list[StageTechniqueRequest]
    model_config = ConfigDict(extra="forbid")
