"""thigh_link.py — 42 mm hip_pitch -> knee structural link.

Carries TWO ST-3215-C018 bodies: hip_pitch near the top and knee near the
bottom. Both output axes are parallel to Y, 42 mm apart vertically. The top
servo's horn (fixed to the hip_mount) pitches this link; the bottom servo's
horn drives the shin. MR63ZZ pivot support at each axis.

ST-3215 shaft dir = 35 mm; with output axis || Y, the pocket is
Y = 35.4 (shaft), X = 45.6 (body long), Z = 25.1 (body height), +0.4 clearance.

Local frame: origin ON the hip_pitch output axis (top pivot), +Z down-negative
toward the knee (knee axis at Z=-42), +Y along the output shafts. cfg side L/R
(mirrored across sagittal in assembly).
"""
import sys
import json
import pathlib
import cadquery as cq

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "lib"))
with open(_HERE.parent.parent / "dims" / "dimensions.json", encoding="utf-8") as _f:
    D = json.load(_f)
from fasteners import clearance_hole  # noqa: E402

S = D["st3215_c018"]
MR63 = D["bearing_mr63"]
BL, BW, BH = S["body"]["l"], S["body"]["w"], S["body"]["h"]   # 45.2 x 24.7 x 35
SHAFT_D = S["shaft"]["outer_d"]
THIGH = 42.0                                  # hip_pitch output -> knee axis
POCKET = 0.4

META = {
    "part_id": "thigh_link",
    "name": "Thigh link (2x ST-3215, PETG)",
    "bom_line": "§2 #13",
    "qty": 2,
    "mass_g": 55.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: origin on the hip_pitch output axis (top pivot), knee "
        "axis at Z=-42 (realizes the 42 mm thigh pivot-to-pivot), output axes "
        "parallel Y. cfg['side'] L/R; assembly mirrors across sagittal plane. "
        "Pockets = body 45.2(X) x 24.7(Z) x 35(Y shaft) +0.4. Bore "
        "+0.18 over 5.9 shaft; MR63ZZ (D=6) pocket concentric at each pivot. "
        "Servo mount holes [EST] as per hip_mount."
    ),
    "print_note": (
        "Print on edge (beam vertical on bed) so the two Y-axis bores print "
        "clean/round; 1.8 mm side walls, web between pockets ~17 mm. No supports."
    ),
}


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


def build(cfg=None):
    cfg = cfg or {}
    side = cfg.get("side", "L")

    px, py, pz = BL + POCKET, BH + POCKET, BW + POCKET   # 45.6, 35.4, 25.1
    beam_x, beam_y = px + 5.0, py + 3.0                  # web width X, thickness Y
    z_top, z_knee = 0.0, -THIGH
    z_lo, z_hi = z_knee - pz / 2.0 - 3.0, z_top + pz / 2.0 + 3.0

    beam = (cq.Workplane("XY")
            .box(beam_x, beam_y, z_hi - z_lo)
            .translate((0, 0, (z_hi + z_lo) / 2.0)))

    # Two servo pockets (top = hip_pitch, bottom = knee).
    for zc in (z_top, z_knee):
        pocket = cq.Workplane("XY").box(px, py, pz).translate((0, 0, zc))
        beam = beam.cut(pocket)

    # Output bores along Y at each pivot, +0.18 over 5.9.
    bore_r = (SHAFT_D + 0.18) / 2.0
    for zc in (z_top, z_knee):
        beam = beam.cut(_cyl("Y", beam_y + 10.0, bore_r, 0, 0, zc))
        # MR63 press pocket on +Y face.
        beam = beam.cut(_cyl("Y", MR63["B"] + 0.2, MR63["D"] / 2.0 - 0.05,
                             0, beam_y / 2.0 - (MR63["B"] + 0.2) / 2.0, zc))

    # Servo mounting holes through +Y wall at JSON coords (u->X, v->Z).
    hole_r = clearance_hole("M2") / 2.0
    for zc in (z_top, z_knee):
        for (u, v) in S["mount"]["holes"]:
            x = u - BL / 2.0
            z = zc + (v - BW / 2.0)
            beam = beam.cut(_cyl("Y", beam_y + 10.0, hole_r, x, 0, z))

    out = beam.val()
    out._lafp_side = side
    return out
