"""battery_tray.py — low LiPo cradle for the 3S 2200 pack.

Holds the pack 105x34.5x26 with 0.5 mm slip clearance, two 25 mm strap slots,
an XT60 exit notch, and mounting bosses down to the trunk floor. Sits in the
LOW trunk (below the carrier) to keep CoM low.

Local frame: origin on the tray base centre (pack 105 along X, 34.5 along Y,
26 along Z), Z=0 on the underside of the base plate, +Z up. XT60 exits +X.
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

PACK = D["lipo_3s_2200"]
PL, PW, PH = PACK["size"]                     # 105 x 34.5 x 26
SLIP = 0.5
BASE_T = 3.0

META = {
    "part_id": "battery_tray",
    "name": "LiPo cradle tray (PETG)",
    "bom_line": "§2 #10",
    "qty": 1,
    "mass_g": 35.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: tray base centre, pack 105 along X / 34.5 along Y / 26 "
        "along Z, Z=0 underside of base, XT60 exit +X. Pocket = pack +0.5 slip "
        "per CONVENTIONS §5. Pack size 105x34.5x26 verified (Zeee); strap "
        "slots 25 mm wide per task; tray bolts to trunk floor with 4x M3 bosses."
    ),
    "print_note": (
        "Print base flat on bed; side retainer walls up. Open +X end for the "
        "XT60 + balance lead exit. ~3 mm base, 2 mm walls, no supports."
    ),
}


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


def build(cfg=None):
    cfg = cfg or {}
    # Cavity is 107 mm wide (outer bbox 111 - 2x2 wall); tray base = PL + 1.0
    # = 106 so it drops in with ~0.5 mm margin per side (clash fix round 2).
    tray_x = PL + 1.0
    tray_y = PW + 6.0
    wall_h = PH + BASE_T
    # Base plate.
    base = cq.Workplane("XY").box(tray_x, tray_y, BASE_T).translate((0, 0, BASE_T / 2.0))

    # Two long-side retainer walls (along X). Pocket width = PW + slip; walls
    # span X -52..+40 (the +X end is left open for the XT60 lead).
    side_y = (PW + SLIP) / 2.0 + 1.5
    for sy in (-side_y, side_y):
        wall = (cq.Workplane("XY")
                .box(92.0, 2.0, wall_h)
                .translate((-6.0, sy, BASE_T + wall_h / 2.0 - 0.5)))
        base = base.union(wall)

    # Low rear lip at -X (a tall end wall won't fit: pack 105 nearly fills 106).
    rear = (cq.Workplane("XY")
            .box(2.0, tray_y, 8.0)
            .translate((-52.0, 0, BASE_T + 4.0)))
    base = base.union(rear)

    # XT60 exit: +X end already open (walls stop at X=+40); cut a generous notch
    # out of the +X base so the discharge/balance lead stub clears the +X wall.
    notch = cq.Workplane("XY").box(22.0, 26.0, 16.0).translate((44.0, 0.0, 8.0))
    base = base.cut(notch)

    # Two 25 mm strap slots through the base (across Y), re-spaced for the 106 tray.
    for sx in (-28.0, -2.0):
        slot = cq.Workplane("XY").box(26.0, tray_y + 2.0, BASE_T + 2.0).translate((sx, 0, BASE_T / 2.0))
        base = base.cut(slot)

    # 4x M3 mounting bosses at the corners down to the trunk floor.
    boss_r = boss_od("M3") / 2.0
    hole_r = clearance_hole("M3") / 2.0
    for bx in (-tray_x / 2.0 + 5.0, tray_x / 2.0 - 5.0):
        for by in (-tray_y / 2.0 + 4.0, tray_y / 2.0 - 4.0):
            boss = _cyl("Z", BASE_T + 4.0, boss_r, bx, by, (BASE_T + 4.0) / 2.0)
            base = base.union(boss)
            base = base.cut(_cyl("Z", BASE_T + 8.0, hole_r, bx, by, (BASE_T + 4.0) / 2.0))

    return base.val()
