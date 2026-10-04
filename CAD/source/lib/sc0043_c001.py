"""Feetech SC-0043-C001 wing/neck micro servo (all-Feetech build, x4).

Dims from dims/dimensions.json key "sc0043_c001". Body 20.3x8.5x19.39,
28T spline shaft OD3.9 protruding 3.1 mm, M1.7 horn retaining screw,
3-pin bus connector + 15 mm exit stub.

Local frame (same convention as the leg servo): origin at the output-shaft
axis on the mounting/top face, shaft +Z, body hanging at z < 0. Rotating
about global Z = rotating the servo about its output axis.
"""
import cadquery as cq

META = {
    "part_id": "sc0043_c001",
    "name": "Feetech SC-0043-C001 wing/neck micro servo (28T, 6.6g)",
    "bom_line": "BOM §6 #4/#5 (SC-0043-C001 wings/neck, x4)",
    "qty": 4,
    "mass_g": 6.6,
    "material": "plastic case / metal gear",
    "source_url": "https://www.feetech.cn/en/559569",
    "origin_note": (
        "local frame: origin at output-shaft axis on the top (20.3x8.5) face, "
        "shaft +Z, body z in [-19.39,0]. Shaft/body centre at local (0,0). "
        "[EST] two mounting ears at x=+/-10.15 (20.3 spacing) with O~2 holes; "
        "[EST] stock horn arm span ~15mm; connector JST family not published (3-pin 15cm verified)."
    ),
    "print_note": "purchased hardware — not printed",
}

# --- dims (dimensions.json: sc0043_c001) ---
BODY_L, BODY_W, BODY_H = 20.3, 8.5, 19.39           # verified
EAR_SPACING = 20.3                                   # [EST] centre-to-centre along length
EAR_HOLE_D = 2.0
SHAFT_D, SHAFT_L = 3.9, 3.1                         # verified
HORN_D = 10.0                                        # [EST] horn disc (span ~15 typical)
HORN_T = 1.5
RETAIN_D = 1.7                                       # M1.7 retaining screw (verified)


def build(cfg=None):
    cfg = cfg or {}

    # --- body box: z from -BODY_H to 0 (top/output face at z=0) ---
    body = (
        cq.Workplane("XY")
        .box(BODY_L, BODY_W, BODY_H)
        .translate((0.0, 0.0, -BODY_H / 2.0))
    )

    # --- two mounting ears at +/-EAR_SPACING/2, with O~2 holes ---
    ear_x = EAR_SPACING / 2.0
    for sx in (-1.0, 1.0):
        ear = (
            cq.Workplane("XY")
            .box(3.3, BODY_W, 5.0)
            .translate((sx * (ear_x + 1.65), 0.0, -2.5))
        )
        body = body.union(ear)
        hole = (
            cq.Workplane("XY")
            .cylinder(6.0, EAR_HOLE_D / 2.0)
            .translate((sx * ear_x, 0.0, -2.5))
        )
        body = body.cut(hole)

    # --- output shaft, z 0 .. SHAFT_L ---
    shaft = (
        cq.Workplane("XY")
        .cylinder(SHAFT_L, SHAFT_D / 2.0)
        .translate((0.0, 0.0, SHAFT_L / 2.0))
    )

    # --- stock horn disc + M1.7 retaining screw ---
    horn = (
        cq.Workplane("XY")
        .cylinder(HORN_T, HORN_D / 2.0)
        .translate((0.0, 0.0, SHAFT_L + HORN_T / 2.0))
    )
    retain = (
        cq.Workplane("XY")
        .cylinder(1.5, RETAIN_D / 2.0)
        .translate((0.0, 0.0, SHAFT_L + HORN_T + 0.75))
    )

    # --- 3-pin connector block on the -X end face + 15 mm exit stub ---
    conn = (
        cq.Workplane("XY")
        .box(4.0, 6.0, 6.0)
        .translate((-BODY_L / 2.0 - 2.0, 0.0, -4.0))
    )
    cable = (
        cq.Workplane("YZ")
        .cylinder(15.0, 0.75)
        .translate((-BODY_L / 2.0 - 4.0 - 7.5, 0.0, -4.0))
    )

    solid = (
        body.union(shaft)
        .union(horn)
        .union(retain)
        .union(conn)
        .union(cable)
    )
    return solid.val()
