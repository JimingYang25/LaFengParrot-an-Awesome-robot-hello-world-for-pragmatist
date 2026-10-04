"""hip_mount.py — trunk-to-leg hip_roll interface (one ST-3215-C018).

Holding ONE leg servo with its output axis parallel to X (frontal abduction).
Left/right built via cfg["side"] in {"L","R"}; the housing is Y-symmetric so the
assembly mirrors it across the sagittal plane (axes at y = +/-17 mm).

ST-3215 body 45.2x24.7x35, shaft normal to the 45.2x24.7 face (so the 35 mm
dimension runs along the output axis = local X). Pocket +0.4 on the body.
MR63ZZ (3x6x2.5) bearing support concentric with the output. Horn clearance
around the +X output. M3 ears up to the trunk floor.

Local frame: origin ON the hip_roll output shaft centre, +X along the shaft
(outboard +X for the left leg), +Y forward/aft along the 45.2 mm body, +Z up.
"""
import sys
import json
import pathlib
import cadquery as cq

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "lib"))
with open(_HERE.parent.parent / "dims" / "dimensions.json", encoding="utf-8") as _f:
    D = json.load(_f)
from fasteners import boss_od, clearance_hole  # noqa: E402

S = D["st3215_c018"]
MR63 = D["bearing_mr63"]
BL, BW, BH = S["body"]["l"], S["body"]["w"], S["body"]["h"]   # 45.2 x 24.7 x 35 (shaft dir = 35)
SHAFT_D = S["shaft"]["outer_d"]               # 5.9
POCKET = 0.4
WALL = 2.5
# Hardware agent re-derives the ST-3215 body offset from the shaft axis along
# X (~5.75 mm, datasheet). The POCKET is centred on that body centre, while the
# shaft bore + 4 JSON mount holes stay ON the shaft axis (X=0). Flip the sign
# here if the hardware module seats the body on -X.
BODY_OFF_X = 5.75

META = {
    "part_id": "hip_mount",
    "name": "Hip roll servo mount (PETG, L/R)",
    "bom_line": "§2 #12",
    "qty": 2,
    "mass_g": 42.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: origin on the hip_roll output shaft centre, +X along the "
        "shaft. cfg['side'] in {L,R}: build identical, assembly mirrors across "
        "sagittal plane (left/right hip_roll axes at y=+/-17 mm, 34 mm apart). "
        "Pocket = body box 45.2(Y) x 24.7(Z) x 35(X) +0.4 on Y/Z faces and "
        "+0.4 on BOTH X sides (clash fix r3). The pocket/housing are centred on "
        "the body centre, offset BODY_OFF_X=5.75 mm along X from the shaft axis "
        "(datasheet offset; sign pending hardware agent), while the shaft bore "
        "and 4 JSON mount holes stay ON the axis X=0. Servo mount holes "
        "[[6.5,2.5],[27.2,2.5],[6.5,22.2],[27.2,22.2]] [EST pixel-measured] "
        "mapped u->Y(45.2), v->Z(24.7). MR63ZZ (D=6 bore 3) pocket concentric "
        "with output; inner-race pilot pin is supplied by the assembly (servo "
        "splined hub is 25T/5.9, larger than the 3 mm bearing bore, so the "
        "bearing locates a coaxial pivot pilot, not the spline itself)."
    ),
    "print_note": (
        "Print with output axis (X) horizontal; the +/-X bearing bores face the "
        "bed and up so they stay round. 2.5 mm walls, 1 mm corner radii; no "
        "supports. Mirror for R side in the slicer if needed."
    ),
}


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


def build(cfg=None):
    cfg = cfg or {}
    side = cfg.get("side", "L")

    # Pocket dims: X = shaft dir = BH(35); Y = BL(45.2); Z = BW(24.7).
    # Pocket gets +0.4 clearance on BOTH X sides (clash fix round 3); the Y/Z
    # faces keep the original +0.4.
    px, py, pz = BH + 2 * 0.4, BL + POCKET, BW + POCKET
    hx, hy, hz = px + 2 * WALL, py + 2 * WALL, pz + 2 * WALL

    # Housing + pocket centred on the BODY centre (offset from the shaft axis).
    block = cq.Workplane("XY").box(hx, hy, hz).translate((BODY_OFF_X, 0, 0))
    pocket = cq.Workplane("XY").box(px, py, pz).translate((BODY_OFF_X, 0, 0))
    part = block.cut(pocket)

    # Output shaft bore along X ON the axis (X=0), +0.18 over 5.9.
    bore_r = (SHAFT_D + 0.18) / 2.0
    part = part.cut(_cyl("X", hx + 20.0, bore_r, 0, 0, 0))
    # MR63ZZ bearing press pocket (D=6 -> 5.95) on the block's +X face.
    face_x = BODY_OFF_X + hx / 2.0
    part = part.cut(_cyl("X", MR63["B"] + 0.2, MR63["D"] / 2.0 - 0.05,
                         face_x - (MR63["B"] + 0.2) / 2.0, 0, 0))

    # Servo mounting screws through the wall at JSON hole coords (M2 clear),
    # drilled along X on the shaft axis plane.
    hole_r = clearance_hole("M2") / 2.0
    for (u, v) in S["mount"]["holes"]:
        y = u - BL / 2.0
        z = v - BW / 2.0
        part = part.cut(_cyl("X", hx + 20.0, hole_r, 0, y, z))

    # Connector notch on the -Z face (servo connector exits bottom).
    part = part.cut(cq.Workplane("XY").box(12.0, 8.0, WALL + 3.0)
                    .translate((BODY_OFF_X, 0, -hz / 2.0 + 1.5)))

    # Two M3 mounting ears reaching UP to the trunk floor (on the block centre).
    ear_h = 18.0
    ear = (cq.Workplane("XY").box(16.0, 8.0, ear_h)
           .translate((0, 0, hz / 2.0 + ear_h / 2.0 - 0.5)))
    ear_l = ear.translate((BODY_OFF_X - hx / 2.0 + 8.0, 0, 0))
    ear_r = ear.translate((BODY_OFF_X + hx / 2.0 - 8.0, 0, 0))
    part = part.union(ear_l).union(ear_r)
    ear_hole_r = clearance_hole("M3") / 2.0
    for ex in (BODY_OFF_X - hx / 2.0 + 8.0, BODY_OFF_X + hx / 2.0 - 8.0):
        part = part.cut(_cyl("Z", ear_h + 6.0, ear_hole_r, ex, 0, hz / 2.0 + ear_h / 2.0))

    # side recorded for the assembly mirror (geometry is Y-symmetric).
    part = part.val()
    part._lafp_side = side
    return part
