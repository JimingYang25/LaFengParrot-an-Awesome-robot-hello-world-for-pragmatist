"""Feetech ST-3215-C018 serial bus leg servo (all-Feetech build variant, x6).

Dims from dims/dimensions.json key "st3215_c018" (datasheet PDF + outline
drawing). Body box 45.2x24.7x35.0, 25T spline shaft OD5.9, octagonal horn
flange OD19.95 with 4x M3 holes + M3x6 retaining screw, 5264-3P 3-pin
connector + 15 mm exit stub on the face opposite the shaft.

Local frame (CONVENTIONS task contract):
  origin = output-shaft axis lying ON the mounting (output) face,
  shaft pointing +Z. The shaft axis is taken as the centroid of the 4
  pixel-measured output-face mount holes, so the hole pattern is symmetric
  in local X/Y. Body hangs behind the face (z < 0); horn/shaft protrude +Z.
  Rotating this part about global Z = rotating the servo about its output
  axis, as the leg kinematics require.
"""
import math
import cadquery as cq

META = {
    "part_id": "st3215_c018",
    "name": "Feetech ST-3215-C018 leg servo (25T, 12V 30kg-cm)",
    "bom_line": "BOM §6 #2/#3 (ST-3215-C018 legs, x6)",
    "qty": 6,
    "mass_g": 55.0,
    "material": "aluminum gearbox / plastic case",
    "source_url": "https://www.feetech.cn/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf",
    "origin_note": (
        "local frame: origin at output-shaft axis on the output (45.2x24.7) face, "
        "shaft +Z, body z in [-35,0]. Shaft axis = centroid of the 4 mount holes "
        "(TL coords 16.85,12.35). Body box center local x=+5.75. "
        "[EST] mount-hole xy pixel-measured off Fig.9 outline; [EST] shaft protrusion ~6mm "
        "from horn/hub section; horn M3x6 retaining screw = datasheet-verified (NOT M2)."
    ),
    "print_note": "purchased hardware — not printed",
}

# --- dims (dimensions.json: st3215_c018) ---
BODY_L, BODY_W, BODY_H = 45.2, 24.7, 35.0          # verified datasheet
HOLES_TL = [[6.5, 2.5], [27.2, 2.5], [6.5, 22.2], [27.2, 22.2]]  # [EST]
HOLE_D = 2.2
SHAFT_D, SHAFT_L = 5.9, 6.0                         # shaft OD verified; length [EST]
HORN_FLANGE_D = 19.95                               # verified horn drawing
HORN_FLANGE_T = 2.5
HORN_HUB_D = 8.0
HORN_HUB_T = 4.5
HORN_BCD = 14.0                                     # 4x M3 on ~14mm BCD
HORN_M3_D = 3.0
RETAIN_D, RETAIN_L = 3.0, 6.0                       # M3x6 retaining screw (datasheet 6-13)

# shaft axis = centroid of the 4 [EST] mount holes (TL = top-left of 45.2x24.7 face)
_AX = (HOLES_TL[0][0] + HOLES_TL[1][0]) / 2.0        # 16.85
_AY = (HOLES_TL[0][1] + HOLES_TL[2][1]) / 2.0        # 12.35
# body box centre in local coords. Body TL edge spans x=0..45.2; local x = TL - _AX,
# so body centre = (BODY_L/2 - _AX) = 22.6 - 16.85 = +5.75. The body extends
# -16.85 .. +28.35 about the shaft (long tail to +X).
_BODY_CX = BODY_L / 2.0 - _AX                        # +5.75
_BODY_CY = _AY - BODY_W / 2.0                        # 0.0


def build(cfg=None):
    cfg = cfg or {}
    shaft_len = cfg.get("shaft_length", SHAFT_L)

    # --- body box: z from -BODY_H to 0 (output face at z=0) ---
    body = (
        cq.Workplane("XY")
        .box(BODY_L, BODY_W, BODY_H)
        .translate((_BODY_CX, _BODY_CY, -BODY_H / 2.0))
    )

    # --- 4 output-face mount holes ([EST] coords), drilled from z=0 back 8 mm ---
    for (hx, hy) in HOLES_TL:
        hx_l = hx - _AX
        hy_l = hy - _AY
        hole = (
            cq.Workplane("XY")
            .cylinder(8.0, HOLE_D / 2.0)
            .translate((hx_l, hy_l, -4.0))
        )
        body = body.cut(hole)

    # --- output spline shaft, z 0 .. shaft_len ---
    shaft = (
        cq.Workplane("XY")
        .cylinder(shaft_len, SHAFT_D / 2.0)
        .translate((0.0, 0.0, shaft_len / 2.0))
    )

    # --- horn: flange disc + hub, sitting near the shaft tip ---
    flange_z0 = shaft_len - 2.5                       # flange thk 2.5
    horn = (
        cq.Workplane("XY")
        .cylinder(HORN_FLANGE_T, HORN_FLANGE_D / 2.0)
        .translate((0.0, 0.0, flange_z0 + HORN_FLANGE_T / 2.0))
    )
    hub = (
        cq.Workplane("XY")
        .cylinder(HORN_HUB_T, HORN_HUB_D / 2.0)
        .translate((0.0, 0.0, flange_z0 + HORN_HUB_T / 2.0 - 1.0))
    )
    # 4x M3 tapped holes on ~14 mm BCD, through the flange
    for k in range(4):
        ang = math.radians(45.0 + 90.0 * k)
        hx = (HORN_BCD / 2.0) * math.cos(ang)
        hy = (HORN_BCD / 2.0) * math.sin(ang)
        h = (
            cq.Workplane("XY")
            .cylinder(HORN_FLANGE_T + 1.0, HORN_M3_D / 2.0)
            .translate((hx, hy, flange_z0 + HORN_FLANGE_T / 2.0))
        )
        horn = horn.cut(h)
    # M3x6 retaining screw head on top of the hub (simplified as a short cylinder)
    retain = (
        cq.Workplane("XY")
        .cylinder(2.5, RETAIN_D / 2.0)
        .translate((0.0, 0.0, shaft_len + 1.25))
    )

    # --- 5264-3P connector block on the back face (z=-BODY_H) + 15 mm exit stub ---
    conn = (
        cq.Workplane("XY")
        .box(16.0, 10.0, 6.0)
        .translate((_BODY_CX, 0.0, -BODY_H - 3.0))
    )
    cable = (
        cq.Workplane("XY")
        .cylinder(15.0, 1.25)
        .translate((_BODY_CX, 0.0, -BODY_H - 6.0 - 7.5))
    )

    solid = (
        body.union(shaft)
        .union(horn)
        .union(hub)
        .union(retain)
        .union(conn)
        .union(cable)
    )
    return solid.val()
