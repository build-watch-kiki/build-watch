import math
from datetime import date
from typing import Annotated, Generic, Self, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, Field, ConfigDict, computed_field, model_validator
from pydantic.alias_generators import to_camel

from buildwatch.shared.exceptions import WrongDatesException

T = TypeVar("T")
M = TypeVar("M", default="MetadataResponse")


class AppBaseModel(BaseModel):
    """Базовая схема с camelCase-алиасами"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PaginationSchema(AppBaseModel):
    """Параметры пагинации"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=1000)


PaginationDep = Annotated[PaginationSchema, Depends(PaginationSchema)]


class DateRange(AppBaseModel):
    """Диапазон дат для фильтрации"""

    start_dt: date | None = Field(
        default=None, serialization_alias="startDate", validation_alias="startDate"
    )
    end_dt: date | None = Field(
        default=None, serialization_alias="endDate", validation_alias="endDate"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        """Проверка интервала дат если обе указаны"""

        if self.start_dt and self.end_dt:
            if self.start_dt >= self.end_dt:
                raise WrongDatesException
        return self


class SearchRequest(PaginationSchema):
    """Параметры поиска с пагинацией"""

    search: Annotated[str | None, Field(default=None, alias="search_value")]


SearchRequestDep = Annotated[SearchRequest, Depends(SearchRequest)]


class ProjectSearchRequest(SearchRequest, DateRange):
    """Параметры поиска проектов/этапов с фильтрацией по датам"""


ProjectSearchRequestDep = Annotated[ProjectSearchRequest, Depends(ProjectSearchRequest)]


class PaginationResponse(PaginationSchema):
    """Ответ с пагинацией и общим количеством страниц"""

    total: int = Field(default=0, ge=0)

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.total == 0 or self.page_size == 0:
            return 0
        return math.ceil(self.total / self.page_size)


class MetadataResponse(PaginationResponse):
    """Метаданные пагинации для списка"""


class GanttMetadata(AppBaseModel):
    """Метаданные для Ганта — без page/page_size"""

    total: int = Field(default=0, ge=0)
    limit: int | None = Field(default=None, ge=1, le=1000)


class StageGanttRequest(AppBaseModel):
    """Необязательные фильтры Ганта; без них возвращается весь проект."""

    from_dt: date | None = Field(
        default=None,
        alias="from",
        validation_alias="from",
        serialization_alias="from",
    )
    to_dt: date | None = Field(
        default=None,
        alias="to",
        validation_alias="to",
        serialization_alias="to",
    )
    limit: int | None = Field(default=None, ge=1, le=1000)
    parent_id: int | None = Field(default=None, alias="parentId")

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.from_dt and self.to_dt and self.from_dt > self.to_dt:
            raise WrongDatesException
        return self


def _get_stage_gantt_request(
    from_param: Annotated[date | None, Query(alias="from")] = None,
    to_param: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = None,
    parent_id: Annotated[int | None, Query(alias="parentId")] = None,
) -> StageGanttRequest:
    """Зависимость с корректными alias from/to (обходит keyword-проблему Pydantic Depends)"""

    data: dict = {}
    if from_param is not None:
        data["from"] = from_param
    if to_param is not None:
        data["to"] = to_param
    if parent_id is not None:
        data["parentId"] = parent_id
    if limit is not None:
        data["limit"] = limit
    return StageGanttRequest.model_validate(data)


StageGanttRequestDep = Annotated[StageGanttRequest, Depends(_get_stage_gantt_request)]


class DeadlinesSchema(AppBaseModel):
    """Базовый класс с валидацией start_dt < end_dt"""

    start_dt: date = Field(
        serialization_alias="startDate", validation_alias="startDate"
    )
    end_dt: date = Field(serialization_alias="endDate", validation_alias="endDate")

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        """Проверка start_dt < end_dt"""

        if self.start_dt >= self.end_dt:
            raise WrongDatesException
        return self


class OptionalDeadlinesSchema(AppBaseModel):
    """Базовый класс с опциональными датами"""

    start_dt: date | None = Field(
        default=None, serialization_alias="startDate", validation_alias="startDate"
    )
    end_dt: date | None = Field(
        default=None, serialization_alias="endDate", validation_alias="endDate"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        """Проверка интервала дат если обе указаны"""

        if self.start_dt and self.end_dt:
            if self.start_dt >= self.end_dt:
                raise WrongDatesException
        return self


class BaseDetailSchema(AppBaseModel, Generic[T, M]):
    """Обёртка списка с метаданными — M дженерик (MetadataResponse по умолчанию)"""

    items: list[T]
    metadata: M = Field(default_factory=lambda: MetadataResponse())  # type: ignore[arg-type]
