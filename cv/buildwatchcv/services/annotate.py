"""TEMP-DEBUG: отрисовка bbox поверх фото для локального дампа.

Временная мера, на проде не будет — удалить вместе с debug_dump.py
и шагом 4 в pipeline.py.
"""

import hashlib
import io
import logging

logger = logging.getLogger(__name__)

_PALETTE: list[tuple[int, int, int]] = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 128, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (255, 128, 0),
    (128, 0, 255),
]


def _color_for(class_name: str) -> tuple[int, int, int]:
    h = int(hashlib.md5(class_name.encode("utf-8")).hexdigest(), 16)
    return _PALETTE[h % len(_PALETTE)]


def draw_boxes(image_bytes: bytes, detections: list) -> bytes:
    """Нарисовать bbox детекций поверх изображения. Вернуть JPEG-байты."""
    from PIL import Image, ImageDraw

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    line = max(2, min(w, h) // 300)

    for det in detections:
        b = det.bbox
        x0 = max(0, int(b.x_center - b.w / 2))
        y0 = max(0, int(b.y_center - b.h / 2))
        x1 = min(w, int(b.x_center + b.w / 2))
        y1 = min(h, int(b.y_center + b.h / 2))
        color = _color_for(det.class_name)
        draw.rectangle([x0, y0, x1, y1], outline=color, width=line)

        label = f"{det.class_name} {det.confidence.detection:.0%}"
        try:
            label_w = int(draw.textlength(label))
        except Exception:
            label_w = len(label) * 6
        ty0 = max(0, y0 - 13)
        draw.rectangle([x0, ty0, x0 + label_w + 4, y0], fill=color)
        draw.text((x0 + 2, ty0 + 1), label, fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
