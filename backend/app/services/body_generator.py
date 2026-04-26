"""High-level pipeline: measurements + photo bytes -> .glb file path."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.config import STORAGE_DIR
from app.models.parametric_body import build_body_mesh
from app.models.schemas import BodyMeasurements
from app.services.face_extractor import DEFAULT_SKIN_RGB, extract_face
from app.services.measurement_mapper import map_measurements


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    s = value.lstrip("#")
    if len(s) != 6:
        raise ValueError("skin_tone must be a 6-char hex string")
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def generate(
    params: BodyMeasurements,
    primary_photo: Optional[bytes],
) -> dict:
    job_id = uuid.uuid4().hex[:12]
    job_dir = STORAGE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    if params.skin_tone:
        skin_rgb = _hex_to_rgb(params.skin_tone)
        face_png_path: Optional[Path] = None
    elif primary_photo:
        face_png, skin_rgb = extract_face(primary_photo)
        face_png_path = job_dir / "face.png"
        face_png_path.write_bytes(face_png)
    else:
        skin_rgb = DEFAULT_SKIN_RGB
        face_png_path = None

    proportions = map_measurements(
        height_cm=params.height_cm,
        bust_cm=params.bust_cm,
        waist_cm=params.waist_cm,
        hips_cm=params.hips_cm,
        gender=params.gender,
    )
    mesh = build_body_mesh(proportions, skin_rgb)

    mesh_path = job_dir / "body.glb"
    mesh.export(mesh_path)

    return {
        "job_id": job_id,
        "mesh_path": mesh_path,
        "face_path": face_png_path,
        "stats": {
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "skin_rgb": list(skin_rgb),
            "proportions_m": {
                "height": proportions.height_m,
                "torso_h": proportions.torso_h,
                "leg_h": proportions.leg_h,
                "shoulder_w": proportions.shoulder_width,
            },
        },
    }
