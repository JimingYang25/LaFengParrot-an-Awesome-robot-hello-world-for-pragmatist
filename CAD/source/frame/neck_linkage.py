"""neck_linkage.py — 2-DOF neck (two stacked SC-0043-C001).

neck_yaw (axis || Z) bolted to the trunk top, then a yoke rising to a
neck_pitch servo (axis || Y) ~70 mm above the trunk. The head shell mounts on
the pitch horn.

Local frame: origin ON the neck_yaw output axis at the trunk-top mounting
plane (Z=0 = trunk top, +Z up). neck_pitch axis at Z ~= 70.
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

S = D["sc0043_c001"]
SL, SW, SH = S["body"]["l"], S["body"]["w"], S["body"]["h"]   # 20.3 x 8.5 x 19.39
SHAFT_D = S["shaft"]["outer_d"]
PITCH_Z = 52.0
POCKET = 0.4

META = {
    "part_id": "neck_linkage",
    "name": "Neck yaw+pitch bracket (2x SC-0043, PETG)",
    "bom_line": "§2 #16",
    "qty": 1,
    "mass_g": 30.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: origin on the trunk-top mount plane (Z=0, +Z up); the "
        "base plate sits z=0..3. neck_yaw axis ||Z at the TOP of the yaw block "
        "(z=22.39), body hanging below it so every feature is z>=0 (no cooler "
        "clash). Yoke rises to neck_pitch axis ||Y at Z=52 (shortened per "
        "CONVENTIONS REV-B; pitch block z 46.25..57.75). Pockets = SC-0043 "
        "body +0.4; bores +0.18 over 3.9 shaft. Ear holes [EST] spaced 20.3."
    ),
    "print_note": (
        "Print base flat; yoke on edge. 2 mm walls; the two shaft bores (Z at "
        "yaw, Y at pitch) should face away from supports for roundness."
    ),
}


def _cyl(axis, length, r, cx=0.0, cy=0.0, cz=0.0):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).cylinder(length, r).translate((cx, cy, cz))


def build(cfg=None):
    cfg = cfg or {}

    # Base plate to trunk top (sits ON z=0; nothing hangs below the trunk top).
    base = cq.Workplane("XY").box(44.0, 44.0, 3.0).translate((0, 0, 1.5))
    hr = clearance_hole("M3") / 2.0
    for bx in (-18.0, 18.0):
        for by in (-18.0, 18.0):
            base = base.cut(_cyl("Z", 8.0, hr, bx, by, 1.5))

    # neck_yaw servo: shaft ||Z. Hardware convention = shaft axis at the TOP of
    # the body, body hangs BELOW the axis. Base top is z=3, so the body occupies
    # z=[3, 3+SH] and the shaft bore is at the TOP (z=3+SH), poking up out of the
    # block. Every printed feature is at z>=0 (no carrier-cooler clash).
    body_bot, body_top = 3.0, 3.0 + SH            # 3.0 .. 22.39
    block_h = (body_top + 1.5) - body_bot
    yaw = (cq.Workplane("XY").box(SL + 3.0, SW + 3.0, block_h)
           .translate((0, 0, body_bot + block_h / 2.0)))
    yaw = yaw.cut(cq.Workplane("XY").box(SL + POCKET, SW + POCKET, SH + POCKET)
                  .translate((0, 0, (body_bot + body_top) / 2.0)))
    yaw = yaw.cut(_cyl("Z", 8.0, (SHAFT_D + 0.18) / 2.0, 0, 0, body_top))
    base = base.union(yaw)

    # Yoke riser from the yaw block top up to the shortened pitch servo.
    riser_bot = body_top + 1.5
    riser_top = 48.0
    riser = cq.Workplane("XY").box(20.0, 10.0, riser_top - riser_bot).translate(
        (0, 0, (riser_top + riser_bot) / 2.0))
    base = base.union(riser)

    # neck_pitch servo block at Z=PITCH_Z: shaft ||Y -> body Y = SH(19.39),
    # face XZ = 20.3 x 8.5.
    pitch = cq.Workplane("XY").box(SL + 3.0, SH + 3.0, SW + 3.0).translate((0, 0, PITCH_Z))
    pitch = pitch.cut(cq.Workplane("XY").box(SL + POCKET, SH + POCKET, SW + POCKET)
                      .translate((0, 0, PITCH_Z)))
    pitch = pitch.cut(_cyl("Y", SH + 10.0, (SHAFT_D + 0.18) / 2.0, 0, 0, PITCH_Z))
    base = base.union(pitch)

    return base.val()
