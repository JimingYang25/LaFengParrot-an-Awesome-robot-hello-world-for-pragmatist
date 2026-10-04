"""NVIDIA Jetson Orin Nano Super dev-kit reference carrier + stock cooler.

Dims from dims/dimensions.json key "orin_carrier" (SP-11324-001 Carrier Board
Spec Fig 4-1/4-2). Board 100x79x1.57, overall envelope 103x90.5x34.77 with
feet + SoDIMM module + ATS heatsink + 40 mm fan + top exhaust grille.

Local frame (task contract): origin at board CENTRE, top face of the PCB at
z=0, +Z up (cooler above). JSON connector coords are measured from the PCB
top-LEFT (100x79), so every (tx,ty) is converted as (tx-50, ty-39.5). Feet
hang below the board (-Z); fan exhaust faces +Z so the trunk top-vent aligns.
"""
import cadquery as cq

META = {
    "part_id": "orin_carrier",
    "name": "Orin Nano Super dev-kit carrier + stock cooler",
    "bom_line": "BOM §2 #1 (Orin Nano Super dev kit)",
    "qty": 1,
    "mass_g": 175.0,
    "material": "PCB / aluminum heatsink / plastic fan",
    "source_url": "https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf",
    "origin_note": (
        "local frame: origin at PCB centre, top face z=0, +Z up. JSON coords are "
        "PCB top-left origin -> converted (tx-50, ty-39.5). Board z in [-1.57,0]; "
        "feet to z=-6.57; heatsink/fan/grille stack to z=28 (total ~34.8 envelope). "
        "[EST] all connector xy, mount-hole xy, feet height ~5mm pixel-measured off "
        "Fig 4-1/4-2 raster; board size + envelope + barrel 5.5/2.5/9.5 + 175g = verified."
    ),
    "print_note": "purchased dev kit — not printed; service access (microSD, barrel, USB, 40-pin) must stay unenclosed",
}

# --- dims (dimensions.json: orin_carrier) ---
BOARD_X, BOARD_Y, BOARD_T = 100.0, 79.0, 1.57
FEET_H = 5.0
MOUNT_HOLES_TL = [[4.0, 4.0], [96.0, 4.0], [4.0, 56.0], [96.0, 56.0]]
MOUNT_D = 2.7                                   # M2.5 clearance
# connector TL coords -> local (subtract board centre 50,39.5)
def _loc(tx, ty):
    return (tx - 50.0, ty - 39.5)


def build(cfg=None):
    cfg = cfg or {}

    # --- PCB: z from -BOARD_T to 0 ---
    board = (
        cq.Workplane("XY")
        .box(BOARD_X, BOARD_Y, BOARD_T)
        .translate((0.0, 0.0, -BOARD_T / 2.0))
    )

    # --- 4 corner mount holes + 5 mm feet below ---
    for (tx, ty) in MOUNT_HOLES_TL:
        x, y = _loc(tx, ty)
        hole = (
            cq.Workplane("XY")
            .cylinder(BOARD_T + 1.0, MOUNT_D / 2.0)
            .translate((x, y, -BOARD_T / 2.0))
        )
        board = board.cut(hole)
        foot = (
            cq.Workplane("XY")
            .cylinder(FEET_H + 0.5, 3.0)
            .translate((x, y, -BOARD_T - FEET_H / 2.0 + 0.25))
        )
        board = board.union(foot)

    top = board  # running solid

    def _up(x, y, sx, sy, h, z0=0.0):
        """small connector/box sticking up from the PCB top face (z=0)."""
        return (
            cq.Workplane("XY")
            .box(sx, sy, h)
            .translate((x, y, z0 + h / 2.0))
        )

    # --- DC barrel jack (J16) 5.5/2.5/9.5, modelled as a short barrel ---
    bx, by = _loc(10.0, 66.0)
    barrel = (
        cq.Workplane("XY")
        .cylinder(10.0, 5.5 / 2.0)
        .translate((bx, by, 5.0))
    )
    top = top.union(barrel)

    # --- 40-pin GPIO header (J12), 2x20 @2.54 pitch ~48.4 x 5 mm, h=8 ---
    gx, gy = _loc(35.0, 5.0)
    top = top.union(_up(gx, gy, 48.4, 5.0, 8.0))

    # --- 2x CSI 15-pin flex connectors on left edge ---
    for cty in (21.0, 40.0):
        cx, cy = _loc(3.0, cty)
        top = top.union(_up(cx, cy, 4.0, 18.0, 3.0))

    # --- microSD slot (bottom edge) ---
    sx, sy = _loc(68.0, 62.0)
    top = top.union(_up(sx, sy, 15.0, 12.0, 3.0))

    # --- USB-C (J5) + 2x USB-A (J6/J7) cluster ---
    ux, uy = _loc(25.0, 68.0)
    top = top.union(_up(ux, uy, 8.0, 7.0, 4.0))
    for uax in (42.0, 55.0):
        ax, ay = _loc(uax, 68.0)
        top = top.union(_up(ax, ay, 14.0, 12.0, 8.0))

    # --- top-side cooling stack (centred on fan exhaust / SoDIMM module) ---
    fx, fy = _loc(50.0, 30.0)                       # fan centre ~ (0,-9.5)
    # SoDIMM module bump (component height up to ~16.7 total incl. cooler)
    module = (
        cq.Workplane("XY")
        .box(69.0, 35.0, 4.0)
        .translate((fx, fy, 2.0))
    )
    heatsink = (
        cq.Workplane("XY")
        .box(63.0, 40.0, 8.0)
        .translate((fx, fy, 4.0 + 4.0))             # z 4..12
    )
    fan = (
        cq.Workplane("XY")
        .box(40.0, 40.0, 10.0)
        .translate((fx, fy, 12.0 + 5.0))            # z 12..22
    )
    # top exhaust grille (raised vent frame; trunk top-vent aligns here)
    grille = (
        cq.Workplane("XY")
        .box(46.0, 46.0, 6.0)
        .translate((fx, fy, 22.0 + 3.0))            # z 22..28
    )
    top = top.union(module).union(heatsink).union(fan).union(grille)

    return top.val()
