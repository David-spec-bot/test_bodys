"""Map user measurements to body proportions used by the mesh builder.

This is a simple analytic mapping. When SMPL-X is wired in later, the same
inputs feed into a regressor that produces the 10 shape coefficients (β).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class BodyProportions:
    height_m: float
    head_h: float
    neck_h: float
    torso_h: float
    leg_h: float
    bust_radius: float
    waist_radius: float
    hips_radius: float
    arm_radius_top: float
    arm_radius_bottom: float
    leg_radius_top: float
    leg_radius_bottom: float
    shoulder_width: float


def _circumference_to_radius(circumference_cm: float) -> float:
    return (circumference_cm / 100.0) / (2 * math.pi)


def map_measurements(
    height_cm: float,
    bust_cm: float,
    waist_cm: float,
    hips_cm: float,
    gender: str = "neutral",
) -> BodyProportions:
    height_m = height_cm / 100.0

    # Vitruvian-ish proportions, slightly tuned per gender.
    head_ratio = 0.13
    neck_ratio = 0.04
    torso_ratio = 0.32 if gender != "male" else 0.34
    leg_ratio = 1.0 - head_ratio - neck_ratio - torso_ratio

    bust_r = _circumference_to_radius(bust_cm)
    waist_r = _circumference_to_radius(waist_cm)
    hips_r = _circumference_to_radius(hips_cm)

    # Limb radii are derived from torso radii so they scale together.
    arm_top = waist_r * 0.32
    arm_bot = waist_r * 0.22
    leg_top = hips_r * 0.55
    leg_bot = hips_r * 0.28

    shoulder_w = bust_r * 2.4 if gender != "male" else bust_r * 2.6

    return BodyProportions(
        height_m=height_m,
        head_h=height_m * head_ratio,
        neck_h=height_m * neck_ratio,
        torso_h=height_m * torso_ratio,
        leg_h=height_m * leg_ratio,
        bust_radius=bust_r,
        waist_radius=waist_r,
        hips_radius=hips_r,
        arm_radius_top=arm_top,
        arm_radius_bottom=arm_bot,
        leg_radius_top=leg_top,
        leg_radius_bottom=leg_bot,
        shoulder_width=shoulder_w,
    )
