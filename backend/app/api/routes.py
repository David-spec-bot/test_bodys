from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_BYTES, STORAGE_DIR
from app.models.schemas import BodyMeasurements, GenerateResponse
from app.services.body_generator import generate

router = APIRouter()


async def _read_image(upload: Optional[UploadFile]) -> Optional[bytes]:
    if upload is None:
        return None
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported image type: {upload.content_type}")
    data = await upload.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image too large (max 10MB)")
    return data


@router.post("/generate", response_model=GenerateResponse)
async def generate_body(
    height_cm: float = Form(...),
    bust_cm: float = Form(...),
    waist_cm: float = Form(...),
    hips_cm: float = Form(...),
    gender: str = Form("neutral"),
    skin_tone: Optional[str] = Form(None),
    photo_front: Optional[UploadFile] = File(None),
    photo_side: Optional[UploadFile] = File(None),
):
    try:
        params = BodyMeasurements(
            height_cm=height_cm,
            bust_cm=bust_cm,
            waist_cm=waist_cm,
            hips_cm=hips_cm,
            gender=gender,  # type: ignore[arg-type]
            skin_tone=skin_tone,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    primary = await _read_image(photo_front) or await _read_image(photo_side)
    result = generate(params, primary)

    return GenerateResponse(
        job_id=result["job_id"],
        mesh_url=f"/api/jobs/{result['job_id']}/mesh",
        face_url=(
            f"/api/jobs/{result['job_id']}/face" if result["face_path"] else None
        ),
        stats=result["stats"],
    )


@router.get("/jobs/{job_id}/mesh")
def get_mesh(job_id: str):
    path = STORAGE_DIR / job_id / "body.glb"
    if not path.exists():
        raise HTTPException(404, "Mesh not found")
    return FileResponse(
        path,
        media_type="model/gltf-binary",
        filename="body.glb",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/jobs/{job_id}/face")
def get_face(job_id: str):
    path = STORAGE_DIR / job_id / "face.png"
    if not path.exists():
        raise HTTPException(404, "Face not found")
    return FileResponse(path, media_type="image/png", filename="face.png")
