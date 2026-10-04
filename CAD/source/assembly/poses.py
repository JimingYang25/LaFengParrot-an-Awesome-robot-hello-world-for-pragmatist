"""LaFengParrot assembly poses — REV-B stability rebuild (CONVENTIONS s6/s7).

Global frame: +X beak/forward, +Y left, +Z up. Origin midway between the two
hip_roll output axes at their height (z=0). Legs hang below, trunk above.

REV-B anchors (measured off the on-disk part bboxes, NOT guessed):
  * hip half-spacing HALF = 27 mm (L/R hip axes at y = +/-27; 44 mm-wide soles
    => inner edges at y = +/-5, 10 mm inner gap).
  * trunk shell placed local z=0 (floor underside) -> global 33, roof top
    (local 100) -> global 133.
  * neck_linkage local z=0 (trunk-top plane) -> global 133; pitch axis local
    z=52 -> global 185. head_shell local z=0 (horn plane) -> global 185.
  * orin_carrier board-top (local z=0) -> global 72 (feet bottom ~65.4, cooler
    exhaust ~100, roof vent ~131.5 -> ~31 mm plenum; tray top 64.5 clears feet).
  * battery tray base underside -> global 33 (pack z ~36..62, clears carrier
    feet 64 by 2 mm).

Servo seat rule: align the servo local origin (output-shaft axis on the output
face, z=0) with the pocket bore; the body's built-in +5.75 mm lateral offset
(C018) then lands itself in the pocket centre. Translations were solved by
pocket_centre_global = origin_global + R @ body_centre_local.
"""
from __future__ import annotations
import sys, pathlib
import cadquery as cq
from OCP.gp import gp_Trsf

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import registry  # noqa: E402

# rotation matrices (row-major; v_global = R @ v_local + t); columns = images
# of local X/Y/Z in global coords.
R_ID = [[1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]]

# hip_roll servo: shaft local Z -> global X.
#   L: body-long local X -> global +Y (the +5.75 body tail points OUTBOARD +Y).
R_HIPROLL_L = [[0, 0, 1],
               [1, 0, 0],
               [0, 1, 0]]
#   R: mirror about sagittal (local X -> global -Y) so the +5.75 tail points
#      outboard (-Y); proper 180-deg roll about the shaft.
R_HIPROLL_R = [[0, 0, 1],
               [-1, 0, 0],
               [0, -1, 0]]

# Y-axis shaft servos (hip_pitch / knee / wing / neck-pitch):
#   shaft local Z -> global Y.  local X (body long) -> global X,
#   local Y (body width) -> global Z.
R_PITCHY = [[1, 0, 0],
            [0, 0, 1],
            [0, 1, 0]]
# R-side mirror: shaft local Z -> global -Y (outboard for the right leg/wing).
R_PITCHY_M = [[1, 0, 0],
              [0, 0, -1],
              [0, 1, 0]]


def _loc(R, t):
    tr = gp_Trsf()
    tr.SetValues(R[0][0], R[0][1], R[0][2], t[0],
                 R[1][0], R[1][1], R[1][2], t[1],
                 R[2][0], R[2][1], R[2][2], t[2])
    return cq.Location(tr)


HALF = 27.0            # hip half-spacing (mm)
FLOOR = 33.0           # trunk shell translation (local z=0 -> global)
ROOF = FLOOR + 100.0   # = 133
CARRIER_Z = 72.0       # carrier board-top global (standoff 33 mm [EST])
PITCH_Z = ROOF + 52.0  # neck pitch axis global = 185


# (key, part_id, cfg, R, translation)
_INSTANCES = [
    # ---- legs: hip_mounts on the hip plane ----
    ("hip_mount_L",   "hip_mount",  {"side": "L"}, R_ID,        (0.0,  HALF,  0.0)),
    ("hip_mount_R",   "hip_mount",  {"side": "R"}, R_ID,        (0.0, -HALF,  0.0)),
    # thigh links: hip_pitch pivot 42 mm below the hip plane
    ("thigh_link_L",  "thigh_link", {"side": "L"}, R_ID,        (0.0,  HALF, -42.0)),
    ("thigh_link_R",  "thigh_link", {"side": "R"}, R_ID,        (0.0, -HALF, -42.0)),
    # shin links: knee pivot at z=-84; sole underside local -54 -> global -138.
    ("shin_link_L",   "shin_link",  {"side": "L"}, R_ID,        (0.0,  HALF, -84.0)),
    ("shin_link_R",   "shin_link",  {"side": "R"}, R_ID,        (0.0, -HALF, -84.0)),

    # ---- trunk + internals ----
    ("trunk_shell",   "trunk_shell", None,         R_ID,        (0.0,  0.0,  FLOOR)),
    ("battery_tray",  "battery_tray", None,        R_ID,        (0.0, -23.0, FLOOR)),
    ("power_mount",   "power_mount", None,         R_ID,        (0.0,  23.0, 36.0)),

    # ---- wings (shoulders outboard of the trunk wall) ----
    ("wing_arm_L",    "wing_arm",   {"side": "L"}, R_ID,        (0.0,  62.0, 60.0)),
    ("wing_arm_R",    "wing_arm",   {"side": "R"}, R_ID,        (0.0, -62.0, 60.0)),

    # ---- neck + head on the trunk roof ----
    ("neck_linkage",  "neck_linkage", None,        R_ID,        (0.0,  0.0,  ROOF)),
    ("head_shell",    "head_shell", None,          R_ID,        (0.0,  0.0,  PITCH_Z)),

    # ---- 6x ST-3215 leg servos (origin = shaft axis on output face) ----
    # hip_roll: pocket centre global (5.75, +/-27, 0); body centre local
    # (5.75,0,-17.5) -> R_HIPROLL maps to (-17.5, +/-5.75, 0) => origin solved.
    ("st3215_hiproll_L", "st3215_c018", None, R_HIPROLL_L, (23.25,  HALF - 5.75, 0.0)),
    ("st3215_hiproll_R", "st3215_c018", None, R_HIPROLL_R, (23.25, -HALF + 5.75, 0.0)),
    # hip_pitch: pocket centre (0,+/-27,-42); body centre (5.75,0,-17.5) ->
    # R_PITCHY maps to (5.75,-17.5,0) => origin (-5.75, +/-44.5, -42).
    ("st3215_hippitch_L", "st3215_c018", None, R_PITCHY,    (-5.75,  HALF + 17.5, -42.0)),
    ("st3215_hippitch_R", "st3215_c018", None, R_PITCHY_M,  (-5.75, -HALF - 17.5, -42.0)),
    # knee: pocket centre (0,+/-27,-84)
    ("st3215_knee_L", "st3215_c018", None,     R_PITCHY,    (-5.75,  HALF + 17.5, -84.0)),
    ("st3215_knee_R", "st3215_c018", None,     R_PITCHY_M,  (-5.75, -HALF - 17.5, -84.0)),

    # ---- 4x SC-0043 ----
    # wing: pocket centre (0,+/-62,60); body centre local (0,0,-9.695)
    ("sc0043_wing_L",   "sc0043_c001", None, R_PITCHY,    (0.0,  62.0 + 9.695, 60.0)),
    ("sc0043_wing_R",   "sc0043_c001", None, R_PITCHY_M,  (0.0, -62.0 - 9.695, 60.0)),
    # neck yaw: shaft axis at linkage local z=22.39 -> global 133+22.39
    ("sc0043_neckyaw",  "sc0043_c001", None, R_ID,        (0.0, 0.0, ROOF + 22.39)),
    # neck pitch: pocket centre (0,0,185); body centre (0,0,-9.695)->(0,-9.695,0)
    ("sc0043_neckpitch", "sc0043_c001", None, R_PITCHY,   (0.0, 9.695, PITCH_Z)),

    # ---- carrier (board-top global 70) ----
    ("orin_carrier", "orin_carrier", None, R_ID, (0.0, 0.0, CARRIER_Z)),
    # LiPo pack centre: tray base underside 33, base top 36, half-height 13 -> 49
    ("lipo_3s_2200", "lipo_3s_2200", None, R_ID, (0.0, -23.0, 49.0)),

    # ---- power devices in power_mount channels (translated by its pose) ----
    ("xt60_switch", "xt60_switch", None, R_ID, (-22.0, 23.0, 48.5)),
    ("bec_5v3a",    "bec_5v3a",    None, R_ID, (28.0,  32.5, 43.5)),
    ("fuse_holder", "fuse_holder", None, R_ID, (28.0,  13.5, 43.5)),

    # ---- IMU in the head underside pocket (head-local -12,0,6.5) ----
    ("imuc_icm42688p", "imuc_icm42688p", None, R_ID, (-12.0, 0.0, PITCH_Z + 6.5)),
]

# explode offsets (>=30 mm apart per direction)
_EXPLODE = {
    "head_shell":       (0, 0, 110),
    "imuc_icm42688p":   (0, 0, 110),
    "neck_linkage":     (0, 0, 55),
    "sc0043_neckyaw":    (0, 0, 55),
    "sc0043_neckpitch":  (0, 0, 55),
    "trunk_shell":      (0, 0, 0),
    "orin_carrier":      (0, 100, 0),
    "battery_tray":     (0, 60, 0),
    "lipo_3s_2200":      (0, 60, 0),
    "power_mount":      (0, 130, 0),
    "xt60_switch":      (0, 130, 0),
    "bec_5v3a":         (0, 130, 0),
    "fuse_holder":      (0, 130, 0),
    "hip_mount_L":      (0, 0, -130),
    "hip_mount_R":      (0, 0, -130),
    "thigh_link_L":     (0, 0, -130),
    "thigh_link_R":     (0, 0, -130),
    "shin_link_L":      (0, 0, -130),
    "shin_link_R":      (0, 0, -130),
    "st3215_hiproll_L": (0, 0, -130),
    "st3215_hiproll_R": (0, 0, -130),
    "st3215_hippitch_L": (0, 0, -130),
    "st3215_hippitch_R": (0, 0, -130),
    "st3215_knee_L":    (0, 0, -130),
    "st3215_knee_R":    (0, 0, -130),
    "wing_arm_L":       (0, 80, 0),
    "wing_arm_R":       (0, -80, 0),
    "sc0043_wing_L":    (0, 80, 0),
    "sc0043_wing_R":    (0, -80, 0),
}


def standing() -> dict:
    return {k: _loc(R, t) for (k, _p, _c, R, t) in _INSTANCES}


def exploded() -> dict:
    out = {}
    for (k, _p, _c, R, t) in _INSTANCES:
        dx, dy, dz = _EXPLODE.get(k, (0, 0, 0))
        out[k] = _loc(R, (t[0] + dx, t[1] + dy, t[2] + dz))
    return out


def build_assembly(pose: str = "standing") -> cq.Compound:
    locs = standing() if pose == "standing" else exploded()
    parts = registry.all_parts()
    placed = []
    for (key, pid, cfg, R, t) in _INSTANCES:
        solid = parts[pid]["build"](cfg)
        if isinstance(solid, cq.Workplane):
            solid = solid.val()
        placed.append(solid.located(locs[key]))
    return cq.Compound.makeCompound(placed)


if __name__ == "__main__":
    asm = build_assembly("standing")
    bb = asm.BoundingBox()
    print(f"standing bbox x[{bb.xmin:.1f},{bb.xmax:.1f}] "
          f"y[{bb.ymin:.1f},{bb.ymax:.1f}] z[{bb.zmin:.1f},{bb.zmax:.1f}]")
    print(f"n={len(_INSTANCES)} valid={asm.isValid()} half={HALF}")
