import logging

from buildwatchcv.messages import PhotoUploadedMessage
from buildwatchcv.schemas.bbox import BBox
from buildwatchcv.schemas.confidence import ActivityState, Confidence
from buildwatchcv.schemas.detection import Detection
from buildwatchcv.schemas.image_info import ImageInfo
from buildwatchcv.schemas.processing import ModelInfo, Processing
from buildwatchcv.schemas.response import DetectionResponse
from buildwatchcv.settings import get_settings

logger = logging.getLogger(__name__)


def _yolo_to_detections(yolo_results) -> list[Detection]:
    """Конвертация ultralytics Results -> list[Detection]."""
    detections: list[Detection] = []
    if not yolo_results:
        return detections

    # yolo_results[0].boxes, .names
    result = yolo_results[0]
    names: dict[int, str] = getattr(result, "names", {}) or {}
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    # boxes: xywh, cls, conf
    try:
        xywh = boxes.xywh.cpu().tolist()  # type: ignore
        cls = boxes.cls.cpu().tolist()  # type: ignore
        conf = boxes.conf.cpu().tolist()  # type: ignore
    except Exception:
        # fallback если без .cpu()
        xywh = boxes.xywh.tolist()  # type: ignore
        cls = boxes.cls.tolist()  # type: ignore
        conf = boxes.conf.tolist()  # type: ignore

    for i, (bbox_vals, cls_id, c) in enumerate(zip(xywh, cls, conf)):
        x_c, y_c, w, h = bbox_vals
        cid = int(cls_id)
        cname = names.get(cid, f"class_{cid}")
        # эвристика activity: пока заглушка
        activity = 0.0
        state = ActivityState.UNCERTAIN
        detections.append(
            Detection(
                object_id=i,
                class_id=cid,
                class_name=cname,
                confidence=Confidence(detection=float(c), activity=activity, activity_state=state),
                bbox=BBox(x_center=float(x_c), y_center=float(y_c), w=float(w), h=float(h)),
            )
        )
    return detections


def build_response(
    msg: PhotoUploadedMessage,
    width: int,
    height: int,
    fmt: str,
    yolo_results,
    inference_ms: int,
    version: str | None = None,
) -> DetectionResponse:
    settings = get_settings()
    version = (version or settings.s3.model_version).strip().strip("/")
    bucket = settings.s3.cv_bucket
    models_prefix = settings.s3.models_prefix.strip("/")
    s3_weights = f"s3://{bucket}/{models_prefix}/{version}/best.pt"

    detections = _yolo_to_detections(yolo_results)

    # ImageInfo format маппинг
    fmt_norm = fmt.upper()
    if fmt_norm == "JPG":
        fmt_norm = "JPEG"
    if fmt_norm not in ("JPEG", "PNG", "JPG"):
        fmt_norm = "JPEG"  # type: ignore

    return DetectionResponse(
        image_info=ImageInfo(key=msg.object_path, width=width, height=height, format=fmt_norm),  # type: ignore
        processing=Processing(
            inference_ms=inference_ms,
            model=ModelInfo(name=settings.s3.model_name, version=version, storage_weights=s3_weights),  # type: ignore
        ),
        detections=detections
    )
