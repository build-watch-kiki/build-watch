from pydantic import model_validator

from buildwatchcv.schemas.base import BaseSchema
from buildwatchcv.schemas.image_info import ImageInfo
from buildwatchcv.schemas.processing import Processing
from buildwatchcv.schemas.detection import Detection

class DetectionResponse(BaseSchema):
    """Общий ответ модели."""
    image_info: ImageInfo
    processing: Processing
    detections: list[Detection]
    
    @model_validator(mode="after")
    def _fill_norm_coords(self) -> "DetectionResponse":
        width = self.image_info.width
        height = self.image_info.height
        for det in self.detections:
            bbox = det.bbox
            bbox.x_center_norm = bbox.x_center / width
            bbox.y_center_norm = bbox.y_center / height
            bbox.w_norm = bbox.w / width
            bbox.h_norm = bbox.h / height
        return self