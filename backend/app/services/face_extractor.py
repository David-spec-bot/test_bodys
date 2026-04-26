"""Face detection + crop using MediaPipe.

Returns:
  - cropped face PNG bytes
  - average skin tone sampled from the cheek region (RGB tuple, 0-255)

If MediaPipe isn't available or no face is found, falls back to a center
crop and a default skin tone so the rest of the pipeline can keep going.
"""
from __future__ import annotations

import io
from typing import Optional, Tuple

import numpy as np
from PIL import Image

DEFAULT_SKIN_RGB: Tuple[int, int, int] = (216, 169, 138)


def _load_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)


def _sample_skin_tone(rgb: np.ndarray, box: Tuple[int, int, int, int]) -> Tuple[int, int, int]:
    x1, y1, x2, y2 = box
    h, w = rgb.shape[:2]
    # Sample a small patch around the cheek area (lower-center of the face box).
    cx = (x1 + x2) // 2
    cy = y1 + int((y2 - y1) * 0.65)
    pad = max(4, (x2 - x1) // 12)
    px1 = max(0, cx - pad)
    py1 = max(0, cy - pad)
    px2 = min(w, cx + pad)
    py2 = min(h, cy + pad)
    patch = rgb[py1:py2, px1:px2].reshape(-1, 3)
    if patch.size == 0:
        return DEFAULT_SKIN_RGB
    median = np.median(patch, axis=0).astype(int)
    return tuple(int(c) for c in median)  # type: ignore[return-value]


def _detect_face_box(rgb: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    try:
        import mediapipe as mp
    except ImportError:
        return None

    h, w = rgb.shape[:2]
    with mp.solutions.face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    ) as detector:
        result = detector.process(rgb)
        if not result.detections:
            return None
        # Take the largest detection.
        best = max(
            result.detections,
            key=lambda d: d.location_data.relative_bounding_box.width
            * d.location_data.relative_bounding_box.height,
        )
        bb = best.location_data.relative_bounding_box
        x1 = max(0, int(bb.xmin * w))
        y1 = max(0, int(bb.ymin * h))
        x2 = min(w, int((bb.xmin + bb.width) * w))
        y2 = min(h, int((bb.ymin + bb.height) * h))
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2


def extract_face(image_bytes: bytes) -> Tuple[bytes, Tuple[int, int, int]]:
    """Return (cropped_face_png_bytes, skin_rgb)."""
    rgb = _load_image(image_bytes)
    box = _detect_face_box(rgb)

    if box is None:
        h, w = rgb.shape[:2]
        side = min(h, w) // 2
        cx, cy = w // 2, h // 3
        box = (
            max(0, cx - side // 2),
            max(0, cy - side // 2),
            min(w, cx + side // 2),
            min(h, cy + side // 2),
        )

    x1, y1, x2, y2 = box
    # Pad the box a bit so we get hair / chin context.
    pad_x = int((x2 - x1) * 0.15)
    pad_y = int((y2 - y1) * 0.25)
    h, w = rgb.shape[:2]
    x1p = max(0, x1 - pad_x)
    y1p = max(0, y1 - pad_y)
    x2p = min(w, x2 + pad_x)
    y2p = min(h, y2 + pad_y)

    crop = rgb[y1p:y2p, x1p:x2p]
    skin = _sample_skin_tone(rgb, box)

    out = io.BytesIO()
    Image.fromarray(crop).save(out, format="PNG", optimize=True)
    return out.getvalue(), skin
