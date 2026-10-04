"""wing_arm.py — wing flap (one SC-0043-C001 + printed wing panel).

SC-0043 pocket at the shoulder, output axis || Y (wings spread +/-Y), with a
light flat airfoil-ish panel extending ~90 mm outboard from the shaft.

SC-0043 body 20.3 x 8.5 x 19.39, shaft normal to the top face (28T/3.9,
3.1 mm protrusion). With output axis || Y, Y = 19.39 (body depth), X = 20.3
(length, ear holes spaced 20.3), Z = 8.5 (width).

Local frame: origin ON the shoulder output shaft centre, +Y outboard along the
span (for the left wing). cfg["side"] = "L" -> span +Y; "R" -> span -Y (mirror).
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

S = D["sc0043_c001"]
SL, SW, SH = S["body"]["l"], S["body"]["w"], S["body"]["h"]   # 20.3 x 8.5 x 19.39
SHAFT_D = S["shaft"]["outer_d"]               # 3.9
SPAN = 90.0
POCKET = 0.4

META = {
    "part_id": "wing_arm",
    "name": "Wing arm with printed panel (PETG)",
    "bom_line": "§2 #15",
    "qty": 2,
    "mass_g": 14.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: origin on the shoulder output shaft centre, +Y outboard. "
        "cfg['side'] L: panel extends +Y; R: mirrored to -Y. Pocket = body "
        "20.3(X) x 19.39(Y shaft) x 8.5(Z) +0.4. Ear mount holes: 2 ears spaced "
        "20.3 mm along X (centre hole (10.15,0) on the drawing) [EST]. Shaft "
        "bore +0.18 over 3.9. Panel 90 mm span, ~2 mm thick to keep mass low."
    ),
    "print_note": (
        "Print panel flat on bed (thin Z); shoulder pocket on edge so the Y "
        "shaft bore stays round. 2 mm panel, 1.6 mm pocket walls; no supports."
    ),
}


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


def build(cfg=None):
    cfg = cfg or {}
    side = cfg.get("side", "L")
    sgn = 1.0 if side == "L" else -1.0

    # Pocket block: X = SL(20.3), Y = SH(19.39), Z = SW(8.5).
    px, py, pz = SL + POCKET, SH + POCKET, SW + POCKET
    hx, hy, hz = px + 3.0, py + 3.0, pz + 3.0
    block = cq.Workplane("XY").box(hx, hy, hz)
    block = block.cut(cq.Workplane("XY").box(px, py, pz))

    # Shaft bore along Y, +0.18 over 3.9.
    block = block.cut(_cyl("Y", hy + 10.0, (SHAFT_D + 0.18) / 2.0, 0, 0, 0))
    # Ear mount holes: 2 ears at X = +/-10.15/2? JSON gives hole at (10.15,0)
    # centre spacing 20.3 -> holes at X = +/-10.15, through the top/bottom (Z).
    hr = clearance_hole("M2") / 2.0
    for hx_ in (-SL / 2.0, SL / 2.0):
        block = block.cut(_cyl("Z", hz + 6.0, hr, hx_, 0, 0))

    # Printed wing panel: thin plate extending outboard, chord ~55 in X.
    panel_root = hy / 2.0
    panel = (cq.Workplane("XY")
             .box(55.0, SPAN, 2.0)
             .translate((5.0, sgn * (panel_root + SPAN / 2.0), 0.0)))
    # rounded outboard tip
    tip = _cyl("Z", 2.0, 27.5, 5.0, sgn * (panel_root + SPAN), 0.0)
    block = block.union(panel).union(tip)

    return block.val()
