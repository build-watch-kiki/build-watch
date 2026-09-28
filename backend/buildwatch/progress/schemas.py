from datetime import date, datetime
from typing import Annotated, Literal, Self

from fastapi import Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import Field, ValidationError, model_validator

from buildwatch.photos.schemas import DetectionResponse
from buildwatch.shared.schemas import AppBaseModel

ProgressStatus = Literal["ahead", "on_track", "behind", "unknown"]
DataQuality = Literal["high", "medium", "low", "insufficient"]
MessageSeverity = Literal["info", "warning"]
MessageCategory = Literal["schedule", "technique", "quality", "stage"]
TechniqueStatus = Literal["on_plan", "missing", "unexpected", "quantity_mismatch"]


class ProgressRangeRequest(AppBaseModel):
    from_date: date | None = Field(default=None, alias="from")
    to_date: date | None = Field(default=None, alias="to")

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from must be before or equal to to")
        return self


def get_progress_range_request(
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> ProgressRangeRequest:
    try:
        return ProgressRangeRequest.model_validate({"from": from_date, "to": to_date})
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


ProgressRangeDep = Annotated[ProgressRangeRequest, Depends(get_progress_range_request)]


class ProgressMessageResponse(AppBaseModel):
    code: str
    severity: MessageSeverity
    text: str


class ProgressDetailMessageResponse(ProgressMessageResponse):
    category: MessageCategory
    stage_id: int | None = None
    technique_id: int | None = None
    evidence_photo_ids: list[int] = Field(default_factory=list)


class StageMatchResponse(AppBaseModel):
    id: int
    name: str
    score: float | None


class ProgressStagesResponse(AppBaseModel):
    previous: StageMatchResponse | None
    current: StageMatchResponse | None
    next: StageMatchResponse | None


class DailyProgressSummaryResponse(AppBaseModel):
    date: date
    is_final: bool
    status: ProgressStatus
    deviation_days: int | None
    technique_deviation_count: int
    message: ProgressMessageResponse
    stages: ProgressStagesResponse
    quality: DataQuality


class TechniquePlanFactResponse(AppBaseModel):
    id: int | None
    name: str
    plan: int
    fact: int
    delta: int
    status: TechniqueStatus


class TechniquesResponse(AppBaseModel):
    stage_id: int | None
    items: list[TechniquePlanFactResponse]


class ObservationQualityResponse(AppBaseModel):
    total: int
    usable: int


class ProgressQualityResponse(AppBaseModel):
    level: DataQuality
    observations: ObservationQualityResponse
    coverage: float
    agreement: float
    reasons: list[str]


class EvidencePhotoResponse(AppBaseModel):
    id: int
    url: str
    captured_at: datetime
    reason_codes: list[str]
    detections: list[DetectionResponse] = Field(default_factory=list)


class DailyProgressDetailResponse(DailyProgressSummaryResponse):
    techniques: TechniquesResponse
    messages: list[ProgressDetailMessageResponse]
    quality: ProgressQualityResponse
    evidence: list[EvidencePhotoResponse]


class StageActualProgressResponse(AppBaseModel):
    start_date: date
    end_date: date
    status: ProgressStatus
    deviation_days: int | None
    technique_deviation_count: int
    message: ProgressMessageResponse
