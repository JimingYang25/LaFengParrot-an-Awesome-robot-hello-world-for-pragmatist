"""head_shell.py — parrot head shell on the neck_pitch horn.

Hollow skull + forward beak (+X) + crest on top, 1.6 mm cosmetic walls,
~55x45x50 envelope, with a 20x20 IMU pocket on the underside.

Local frame: origin on the neck_pitch horn mounting plane at the bottom centre
of the skull (Z=0), +Z up, +X forward (beak direction).
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

IMU = D["imuc_icm42688p"]
WALL = 1.6

META = {
    "part_id": "head_shell",
    "name": "Parrot head shell (PETG, hollow)",
    "bom_line": "§2 #17",
    "qty": 1,
    "mass_g": 40.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: bottom-centre horn plane (Z=0), +Z up, +X forward beak. "
        "Skull envelope ~55(X) x 45(Y) x 50(Z), 1.6 mm cosmetic walls per "
        "CONVENTIONS §5. IMU pocket 20x20 on underside matches ICM-42688 "
        "breakout [EST generic GY size]. Neck horn hole on bottom centre."
    ),
    "print_note": (
        "Print upside-down (skull crown on bed) so the beak and crest need no "
        "internal supports; 1.6 mm walls, separate two halves if needed."
    ),
}


def build(cfg=None):
    cfg = cfg or {}
    sx, sy, sz = 55.0, 45.0, 50.0
    cz = 30.0

    # Hollow skull: outer box minus inner cavity (1.6 walls), bottom left closed.
    outer = cq.Workplane("XY").box(sx, sy, sz).translate((0, 0, cz))
    inner = cq.Workplane("XY").box(sx - 2 * WALL, sy - 2 * WALL, sz - 2 * WALL).translate((0, 0, cz))
    head = outer.cut(inner)

    # Beak: tapered cone pointing +X from the face (loft big circle -> small).
    beak = (cq.Workplane("YZ")
            .circle(11.0)
            .workplane(offset=26.0)
            .circle(3.0)
            .loft())
    beak = beak.translate((sx / 2.0 - 2.0, 0.0, cz + 4.0))
    head = head.union(beak)

    # Crest: two thin fins on top.
    for cy in (-6.0, 6.0):
        fin = (cq.Workplane("XY").box(18.0, 2.5, 16.0)
               .rotate((0, 0, 0), (0, 1, 0), -15.0)
               .translate((-8.0, cy, cz + sz / 2.0 + 6.0)))
        head = head.union(fin)

    # Neck horn hole on the bottom centre.
    head = head.cut(cq.Workplane("XY").cylinder(10.0, 6.0).translate((0, 0, 5.0)))

    # IMU pocket recess (20x20) on the underside, offset aft of the horn.
    imu_x, imu_y, imu_z = IMU["size"]
    pocket = cq.Workplane("XY").box(imu_x + 1.0, imu_y + 1.0, 3.0).translate((-12.0, 0, 6.5))
    head = head.cut(pocket)
    for (ix, iy) in IMU["mount_holes"]:
        head = head.cut(cq.Workplane("XY").cylinder(6.0, clearance_hole("M2") / 2.0)
                        .translate((-12.0 + ix - 10.0, iy - 10.0, 6.5)))

    return head.val()
