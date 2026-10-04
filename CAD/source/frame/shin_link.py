"""shin_link.py — 50 mm knee-to-foot link with a fixed rocker sole.

Knee horn attachment at the top (axis || Y), wide foot pad at the bottom.
The sole is not a wheel: its underside has a flat 32 mm centre and two
progressively raised facets at both the toe and heel.  This retains a stable
standing patch while allowing the contact point to roll during a waddle.

Local frame: origin ON the knee axis (top pivot), +Z up, foot pad at Z=-50
(realizes the 50 mm shin length). cfg side L/R (mirrored in assembly).
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
SHAFT_D = S["shaft"]["outer_d"]
SHIN = 50.0

META = {
    "part_id": "shin_link",
    "name": "Shin link with fixed rocker foot (PETG)",
    "bom_line": "§2 #14",
    "qty": 2,
    "mass_g": 26.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: origin on the knee axis (top pivot), +Z up, sole underside "
        "at Z=-54 (leg drop 138 mm unchanged). Knee bore ||Y, +0.18 over 5.9 "
        "shaft, MR63ZZ (D=6) pocket concentric. Fixed sole is 40(X toe->heel) x "
        "44(Y lateral), with a 32 mm flat centre and two rising facets on both "
        "toe and heel; it has no axle or rotating component. At track +/-27 "
        "the L/R sole inner "
        "edges land at y=+/-5 (10 mm inner gap). cfg side L/R mirrored."
    ),
    "print_note": (
        "Print on one side with the 44 mm direction vertical; knee bore remains "
        "horizontal. Use 4 perimeters and 35% gyroid PETG. The symmetric rocker "
        "profile needs no support and avoids a fragile one-layer toe."
    ),
}


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


def build(cfg=None):
    cfg = cfg or {}
    side = cfg.get("side", "L")

    # Vertical web.
    web = cq.Workplane("XY").box(18.0, 8.0, SHIN + 8.0).translate((0, 0, (-SHIN + 8.0) / 2.0))

    # Knee bore along Y at Z=0.
    bore_r = (SHAFT_D + 0.18) / 2.0
    web = web.cut(_cyl("Y", 20.0, bore_r, 0, 0, 0.0))
    web = web.cut(_cyl("Y", MR63["B"] + 0.2, MR63["D"] / 2.0 - 0.05,
                       0, 4.0 - (MR63["B"] + 0.2) / 2.0, 0.0))
    # Knee horn bolt holes: 2x M3 clearance on +/-X around the bore.
    hr = clearance_hole("M3") / 2.0
    web = web.cut(_cyl("Y", 20.0, hr, 7.0, 0, 0.0))
    web = web.cut(_cyl("Y", 20.0, hr, -7.0, 0, 0.0))

    # Fixed compound-rocker sole.  The top stays at z=-50 and joins the web.
    # Underside, heel -> toe:
    #   (-20,-52), (-18,-53.4), (-16,-54), (16,-54),
    #   (18,-53.4), (20,-52)
    # This yields a 32 mm flat standing patch and two progressively steeper
    # facets per end.  The 2 mm end thickness remains practical for PETG.
    sole_profile = [
        (-20.0, -50.0),
        (20.0, -50.0),
        (20.0, -52.0),
        (18.0, -53.4),
        (16.0, -54.0),
        (-16.0, -54.0),
        (-18.0, -53.4),
        (-20.0, -52.0),
    ]
    sole = (cq.Workplane("XZ")
            .polyline(sole_profile)
            .close()
            .extrude(44.0)
            # CadQuery's XZ workplane normal points toward -Y, so +22 centres
            # the 44 mm extrusion on Y=0.
            .translate((0, 22.0, 0)))
    web = web.union(sole)

    out = web.val()
    out._lafp_side = side
    return out
