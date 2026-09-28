from typing import Literal

from buildwatchcv.schemas.base import BaseSchema
from buildwatchcv.schemas.response import DetectionResponse


class CvSucceededEnvelope(BaseSchema):
    cv_run_id: int
    status: Literal["succeeded"] = "succeeded"
    result: DetectionResponse

class CvFailedEnvelope(BaseSchema):
    cv_run_id: int
    status: Literal["failed"] = "failed"
    error: str

CvResultEnvelope = CvSucceededEnvelope | CvFailedEnvelope