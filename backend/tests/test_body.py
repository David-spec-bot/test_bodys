"""Smoke test for the parametric body builder.

Run from backend/:
    python -m pytest tests/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.parametric_body import build_body_mesh  # noqa: E402
from app.services.measurement_mapper import map_measurements  # noqa: E402


def test_mesh_is_watertight_ish():
    p = map_measurements(height_cm=170, bust_cm=88, waist_cm=68, hips_cm=94)
    mesh = build_body_mesh(p, skin_color_rgb=(216, 169, 138))
    assert len(mesh.vertices) > 100
    assert len(mesh.faces) > 100
    # Approximate height check (within 5%).
    extents = mesh.bounds[1] - mesh.bounds[0]
    assert abs(extents[2] - p.height_m) / p.height_m < 0.05


def test_measurements_affect_mesh_extent():
    p_thin = map_measurements(170, 80, 60, 86)
    p_wide = map_measurements(170, 110, 95, 120)
    m_thin = build_body_mesh(p_thin, (200, 200, 200))
    m_wide = build_body_mesh(p_wide, (200, 200, 200))
    extents_thin = m_thin.bounds[1] - m_thin.bounds[0]
    extents_wide = m_wide.bounds[1] - m_wide.bounds[0]
    assert extents_wide[0] > extents_thin[0]
