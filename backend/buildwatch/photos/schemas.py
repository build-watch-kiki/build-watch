import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from buildwatch.shared import AppBaseModel


class ImageBase(BaseModel):
    """Базовая Pydantic-модель изображения"""

    url: str

    model_config = ConfigDict(from_attributes=True)


class ImageResponse(ImageBase):
    """Схема ответа для фото"""

    # id: int
    name: str


class PhotoResponse(AppBaseModel):
    """Фотография проекта и текущий статус её обработки."""

    id: int
    # project_id: int
    name: str
    url: str
    # original_url: str
    detections: list["DetectionResponse"] = Field(default_factory=list)
    captured_at: datetime.datetime | None
    created_at: datetime.datetime
    width: int | None
    height: int | None
    format: str | None
    is_processed: bool
    processing_status: Literal["pending", "succeeded", "failed"]
    model: "PhotoModelResponse | None" = None


class PhotoModelResponse(AppBaseModel):
    name: str
    version: str
    weights: str


class PhotoUploadResponse(AppBaseModel):
    id: int


class PhotoUploadedMessage(BaseModel):
    """Схема сообщения о загруженной фотографии для отправки в брокер сообщений"""

    project_id: int
    cv_run_id: int
    filename: str
    object_path: str
    url: str
    size: int
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    created_at: datetime.datetime | None = None
    uploaded_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConfidenceResponse(AppBaseModel):
    detection: float
    activity: float | None
    activity_state: str | None

    @field_validator("detection", "activity")
    @classmethod
    def round_detection_activity(cls, v: float | None) -> float | None:
        return float(f"{v:.5f}") if v is not None else None


class BBoxResponse(AppBaseModel):
    format: Literal["xywh_center"] = "xywh_center"
    # x_center: float
    # y_center: float
    # w: float
    # h: float
    x_center_norm: float | None
    y_center_norm: float | None
    w_norm: float | None
    h_norm: float | None


class DetectionTechniqueResponse(AppBaseModel):
    id: int
    name: str
    name_ru: str
    color: str


class DetectionResponse(AppBaseModel):
    object_id: int
    class_id: int
    class_name: str
    color: str
    technique: DetectionTechniqueResponse | None = None
    confidence: ConfidenceResponse
    bbox: BBoxResponse


class CVImageInfo(BaseModel):
    key: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    format: str


class CVModelInfo(BaseModel):
    name: str
    version: str
    storage_weights: str


class CVProcessing(BaseModel):
    inference_ms: int = Field(ge=0)
    model: CVModelInfo


class CVConfidence(BaseModel):
    detection: float = Field(ge=0, le=1)
    activity: float | None = Field(default=None, ge=0, le=1)
    activity_state: str | None = None


class CVBBox(BaseModel):
    format: Literal["xywh_center"]
    x_center: float
    y_center: float
    w: float = Field(ge=0)
    h: float = Field(ge=0)
    x_center_norm: float | None = None
    y_center_norm: float | None = None
    w_norm: float | None = None
    h_norm: float | None = None


class CVDetection(BaseModel):
    object_id: int = Field(ge=0)
    class_id: int
    class_name: str
    confidence: CVConfidence
    bbox: CVBBox


class CVResult(BaseModel):
    image_info: CVImageInfo
    processing: CVProcessing
    detections: list[CVDetection]


class CVResultMessage(BaseModel):
    cv_run_id: int
    status: Literal["succeeded", "failed"]
    result: CVResult | None = None
    error: str | None = None
