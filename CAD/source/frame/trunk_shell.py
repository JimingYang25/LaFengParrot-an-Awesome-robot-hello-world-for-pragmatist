"""trunk_shell.py — LaFengParrot trunk enclosure (PETG, printed).

Holds the Jetson Orin Nano Super dev-kit upright (board plane XY, cooler on
top blowing +Z), with 4x M2.5 carrier standoffs, a top vent grille over the
fan exhaust, a +Y service window (microSD / barrel / 40-pin / USB), internal
cable gutters for the FT-SCS bus chain, and screw bosses per CONVENTIONS §5.

Local frame: origin on the sagittal plane at the trunk bottom-floor centre
(X=0 centre, Y=0 centre, Z=0 = underside of floor, +Z up). The assembly
positions this shell so the carrier top lands at the standing trunk height
(~120 mm above the hip plane). Split for printing along the horizontal seam
at Z=50 (upper/lower halves), each <= 220 mm on a side.
"""
import sys
import json
import pathlib
import cadquery as cq

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "lib"))  # so `from fasteners import ...` works
with open(_HERE.parent.parent / "dims" / "dimensions.json", encoding="utf-8") as _f:
    D = json.load(_f)
from fasteners import boss_od, clearance_hole  # noqa: E402

CARRIER = D["orin_carrier"]
M25 = D["fastener_m25"]

WALL = 3.0
IN_X, IN_Y, IN_Z = 105.0, 92.0, 94.0          # cavity (>= 105x92x38 required)
OUT_X = IN_X + 2 * WALL
OUT_Y = IN_Y + 2 * WALL
OUT_Z = 100.0                                 # floor(0..3) + cavity(3..97) + roof(97..100)


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


# Map carrier board coords (origin top-left of 100x79 PCB, +X right +Y down)
# onto the trunk cavity centred frame: board 100(X) x 79(Y) centred on cavity.
def _board_xy(bx, by):
    return (bx - 100.0 / 2.0, by - 79.0 / 2.0)


META = {
    "part_id": "trunk_shell",
    "name": "Trunk shell (PETG, upper/lower split)",
    "bom_line": "§2 #9",
    "qty": 1,
    "mass_g": 230.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: sagittal-plane centre of trunk bottom floor (X=0,Y=0), Z=0 "
        "underside of floor, +Z up. Carrier standoff XY from JSON mount_holes "
        "[EST pixel-measured]; fan-exhaust vent centred on board fan_exhaust "
        "(50,30)->(0,-9.5) [EST]; carrier feet height ~5 [EST] so printed "
        "standoff boss height = 6 mm (incl feet). Service window on +Y wall "
        "gives access to microSD/barrel/40-pin/USB (connector XY all [EST])."
    ),
    "print_note": (
        "Split horizontally at Z=50 into upper (roof+vent) and lower (floor) "
        "halves; each <= 111x98x50, fits 220mm bed. Print roof flat on bed so "
        "the vent grille and mating seam are dimensionally clean; 3 mm walls, "
        "no supports needed for the window rim. Removable +Y service cover "
        "bolts over the window (cover plate is a separate sheet, not modelled)."
    ),
}


def build(cfg=None):
    cfg = cfg or {}
    # Outer box minus inner cavity -> hollow shell (floor 0..3, roof 97..100).
    outer = cq.Workplane("XY").box(OUT_X, OUT_Y, OUT_Z).translate((0, 0, OUT_Z / 2.0))
    inner = cq.Workplane("XY").box(IN_X, IN_Y, IN_Z).translate((0, 0, 3.0 + IN_Z / 2.0))
    shell = outer.cut(inner)

    # 4x M2.5 carrier standoffs rising from the cavity floor (z=3..9, h=6 incl feet).
    boss_r = boss_od("M2.5") / 2.0
    hole_r = clearance_hole("M2.5") / 2.0
    for (bx, by) in CARRIER["mount_holes"]:
        x, y = _board_xy(bx, by)
        boss = _cyl("Z", 6.0, boss_r, x, y, 6.0)
        shell = shell.union(boss)
        shell = shell.cut(_cyl("Z", 12.0, hole_r, x, y, 6.0))

    # Top vent grille: >=60x45 slots directly over the fan exhaust (board 50,30).
    fx, fy = _board_xy(*CARRIER["connectors"]["fan_exhaust"])
    for yy in (-28, -20, -12, -4, 4, 12):
        slot = cq.Workplane("XY").box(52.0, 3.5, 10.0).translate((fx, fy + yy, 98.5))
        shell = shell.cut(slot)

    # +Y service window (microSD / barrel / 40-pin / USB access).
    window = cq.Workplane("XY").box(80.0, 12.0, 62.0).translate((0.0, 49.0, 52.0))
    shell = shell.cut(window)

    # Internal cable gutters: two vertical ribs on the -Y inner wall forming a
    # channel for the FT-SCS leg/wing bus chain.
    for gx in (-30.0, -18.0):
        rib = cq.Workplane("XY").box(6.0, 8.0, 80.0).translate((gx, -42.0, 46.0))
        shell = shell.union(rib)

    return shell.val()
