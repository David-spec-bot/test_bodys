"""Build a parametric humanoid mesh from body proportions.

This is a simple primitive-based stand-in for a real parametric model
(SMPL-X). It builds a lofted torso whose bust/waist/hips circumferences
match the user inputs, with cylindrical limbs and a spherical head.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import trimesh

from app.services.measurement_mapper import BodyProportions

SEGMENTS = 32


def _ring(radius_x: float, radius_y: float, z: float, segments: int = SEGMENTS) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False)
    x = radius_x * np.cos(angles)
    y = radius_y * np.sin(angles)
    z_arr = np.full_like(x, z)
    return np.stack([x, y, z_arr], axis=1)


def _loft(rings: List[np.ndarray], close_top: bool = True, close_bottom: bool = True) -> trimesh.Trimesh:
    """Connect a stack of rings into a closed mesh."""
    n_rings = len(rings)
    seg = rings[0].shape[0]
    verts = np.concatenate(rings, axis=0)
    faces: List[List[int]] = []

    for i in range(n_rings - 1):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            c = (i + 1) * seg + (j + 1) % seg
            d = (i + 1) * seg + j
            faces.append([a, b, c])
            faces.append([a, c, d])

    if close_bottom:
        center_idx = len(verts)
        verts = np.vstack([verts, rings[0].mean(axis=0)])
        for j in range(seg):
            a = j
            b = (j + 1) % seg
            faces.append([center_idx, b, a])

    if close_top:
        center_idx = len(verts)
        verts = np.vstack([verts, rings[-1].mean(axis=0)])
        last = (n_rings - 1) * seg
        for j in range(seg):
            a = last + j
            b = last + (j + 1) % seg
            faces.append([center_idx, a, b])

    return trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)


def _build_torso(p: BodyProportions, z_bottom: float) -> trimesh.Trimesh:
    """Lofted torso: hips → waist → bust → shoulders.

    The torso is mildly elliptical (front-back is shallower than side-side).
    """
    h = p.torso_h
    # Heights along the torso (relative to z_bottom).
    z_hips = z_bottom
    z_waist = z_bottom + h * 0.45
    z_bust = z_bottom + h * 0.78
    z_shoulder = z_bottom + h

    depth_factor = 0.72  # body is shallower front-to-back than side-to-side
    shoulder_r = p.shoulder_width / 2.0

    rings = [
        _ring(p.hips_radius, p.hips_radius * depth_factor, z_hips),
        _ring(p.hips_radius * 0.95, p.hips_radius * 0.85 * depth_factor, z_bottom + h * 0.2),
        _ring(p.waist_radius, p.waist_radius * depth_factor, z_waist),
        _ring(p.bust_radius, p.bust_radius * depth_factor, z_bust),
        _ring(shoulder_r, shoulder_r * depth_factor * 0.9, z_shoulder),
    ]
    return _loft(rings, close_top=True, close_bottom=True)


def _build_limb(
    radius_top: float,
    radius_bottom: float,
    length: float,
    origin: Tuple[float, float, float],
    direction: str = "down",
) -> trimesh.Trimesh:
    """Tapered cylinder. direction='down' means it extends along -Z."""
    n_rings = 6
    rings: List[np.ndarray] = []
    for i in range(n_rings):
        t = i / (n_rings - 1)
        r = radius_top * (1 - t) + radius_bottom * t
        z = -t * length if direction == "down" else t * length
        rings.append(_ring(r, r, z))

    mesh = _loft(rings, close_top=True, close_bottom=True)
    mesh.apply_translation(np.array(origin))
    return mesh


def _build_head(p: BodyProportions, z_top_of_neck: float) -> trimesh.Trimesh:
    radius = p.head_h / 2.0
    head = trimesh.creation.icosphere(subdivisions=3, radius=radius)
    # Slightly squash on the front-back axis to feel less like a soccer ball.
    head.apply_scale([1.0, 0.92, 1.05])
    head.apply_translation([0.0, 0.0, z_top_of_neck + radius])
    return head


def _build_neck(p: BodyProportions, z_bottom: float) -> trimesh.Trimesh:
    r = p.bust_radius * 0.32
    rings = [
        _ring(r * 1.2, r * 1.1, z_bottom),
        _ring(r, r * 0.95, z_bottom + p.neck_h),
    ]
    return _loft(rings, close_top=True, close_bottom=True)


def build_body_mesh(p: BodyProportions, skin_color_rgb: Tuple[int, int, int]) -> trimesh.Trimesh:
    """Assemble the full body mesh, centered at feet (z=0)."""
    z_feet = 0.0
    z_hips = p.leg_h
    z_shoulder = z_hips + p.torso_h
    z_neck_top = z_shoulder + p.neck_h

    torso = _build_torso(p, z_bottom=z_hips)
    neck = _build_neck(p, z_bottom=z_shoulder)
    head = _build_head(p, z_top_of_neck=z_neck_top)

    # Legs hang from hip ring; offset along ±X by half a hip width.
    leg_offset_x = p.hips_radius * 0.55
    left_leg = _build_limb(
        p.leg_radius_top, p.leg_radius_bottom, p.leg_h,
        origin=(-leg_offset_x, 0.0, z_hips),
    )
    right_leg = _build_limb(
        p.leg_radius_top, p.leg_radius_bottom, p.leg_h,
        origin=(leg_offset_x, 0.0, z_hips),
    )

    # Arms hang from shoulders.
    arm_offset_x = p.shoulder_width / 2.0 + p.arm_radius_top * 0.6
    arm_length = p.height_m * 0.42
    left_arm = _build_limb(
        p.arm_radius_top, p.arm_radius_bottom, arm_length,
        origin=(-arm_offset_x, 0.0, z_shoulder),
    )
    right_arm = _build_limb(
        p.arm_radius_top, p.arm_radius_bottom, arm_length,
        origin=(arm_offset_x, 0.0, z_shoulder),
    )

    body = trimesh.util.concatenate([torso, neck, head, left_leg, right_leg, left_arm, right_arm])

    # Apply uniform vertex color so the .glb carries skin tone.
    body.visual.vertex_colors = np.tile(
        np.array([*skin_color_rgb, 255], dtype=np.uint8), (len(body.vertices), 1)
    )
    return body
