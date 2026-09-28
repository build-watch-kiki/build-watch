from pydantic import Field
from buildwatchcv.schemas.base import BaseSchema

class BBox(BaseSchema):
    """Координаты обнаруженной техники."""
    format: str = "xywh_center"
    x_center: float
    y_center: float
    w: float
    h: float
    x_center_norm: float | None = Field(default=None, ge=0.0, le=1.0)
    y_center_norm: float | None = Field(default=None, ge=0.0, le=1.0)
    w_norm: float | None = Field(default=None, ge=0.0, le=1.0)
    h_norm: float | None = Field(default=None, ge=0.0, le=1.0)
    