from typing import Literal, Optional

from pydantic import BaseModel, Field


class BodyMeasurements(BaseModel):
    """User-provided body parameters in centimeters."""

    height_cm: float = Field(..., gt=80, lt=230, description="Total body height")
    bust_cm: float = Field(..., gt=40, lt=200, description="Bust circumference")
    waist_cm: float = Field(..., gt=30, lt=200, description="Waist circumference")
    hips_cm: float = Field(..., gt=40, lt=220, description="Hip circumference")
    gender: Literal["female", "male", "neutral"] = "neutral"
    skin_tone: Optional[str] = Field(
        None, description="Hex color override, e.g. '#d8a98a'"
    )


class GenerateResponse(BaseModel):
    job_id: str
    mesh_url: str
    face_url: Optional[str] = None
    stats: dict
