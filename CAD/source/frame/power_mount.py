"""power_mount.py — trunk-internal bracket for the 5V/3A BEC, XT60 switch and
inline fuse holder, with clear access and cable exits.

Local frame: origin on the bracket plate centre (mounts against the trunk
floor / a wall), +Z up. BEC (30x20x10), switch body (50x25x20), fuse holder
(30x15x10) all [EST] generic sizes from dimensions.json.
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

BEC = D["bec_5v3a"]
SW = D["xt60_switch"]
FUSE = D["fuse_holder"]

META = {
    "part_id": "power_mount",
    "name": "BEC / XT60 switch / fuse bracket (PETG)",
    "bom_line": "§2 #11",
    "qty": 1,
    "mass_g": 28.0,
    "material": "PETG",
    "source_url": "n/a",
    "origin_note": (
        "local frame: bracket plate centre, +Z up, bolts to trunk floor. "
        "BEC 30x20x10, XT60 switch body 50x25x20, fuse holder 30x15x10 are all "
        "[EST] generic sizes (dimensions.md register #10-13); pockets use +0.5 "
        "clearance. Cable exits left open on both short ends."
    ),
    "print_note": (
        "Print plate flat; retainer walls up. Zip-tie posts hold the BEC; the "
        "switch and fuse holder sit in open channels (leads exit both ends)."
    ),
}


def build(cfg=None):
    cfg = cfg or {}
    # Plate footprint <= ~99x44 to clear the trunk service-window rim.
    px, py, pt = 96.0, 42.0, 2.5
    wall = 1.5
    plate = cq.Workplane("XY").box(px, py, pt).translate((0, 0, pt / 2.0))

    def channel(cx, cy, L, W, H, stop_neg_x=False):
        nonlocal plate
        for sy in (-(W / 2.0 + wall), (W / 2.0 + wall)):
            w = (cq.Workplane("XY").box(L + 2 * wall, wall, H)
                 .translate((cx, cy + sy, pt + H / 2.0)))
            plate = plate.union(w)
        if stop_neg_x:
            stop = (cq.Workplane("XY").box(wall, W + 2 * wall, H)
                    .translate((cx - L / 2.0 - wall / 2.0, cy, pt + H / 2.0)))
            plate = plate.union(stop)

    # Seated device bboxes (board body only; leads cosmetic), each pocket +0.5.
    # Layout (X right, Y across):
    #   switch  centre (-22, 0)   50.5 x 25.5 x 20.5  -> X[-47.5, 3], Y[-13, 13]
    #   BEC     centre (+28, +9.5) 30.5 x 20.5 x 10.5 -> X[12.75, 43.25], Y[-0.75,19.75]
    #   fuse    centre (+28, -9.5) 30.5 x 15.5 x 10.5 -> X[12.75, 43.25], Y[-17.25,-1.75]
    # Gaps: switch->right block 9.75 mm in X; BEC->fuse 1 mm in Y. No overlap.
    sw_l, sw_w, sw_h = SW["switch_body"]
    channel(-22.0, 0.0, sw_l + 0.5, sw_w + 0.5, sw_h + 0.5, stop_neg_x=True)

    bl, bw, bh = BEC["size"]
    channel(28.0, 9.5, bl + 0.5, bw + 0.5, bh + 0.5)

    fl, fw, fh = FUSE["holder_body"]
    channel(28.0, -9.5, fl + 0.5, fw + 0.5, fh + 0.5)

    # Cable exit notches on both short ends.
    plate = plate.cut(cq.Workplane("XY").box(6.0, 14.0, 8.0).translate((-px / 2.0 + 1.0, 0, pt + 4.0)))
    plate = plate.cut(cq.Workplane("XY").box(6.0, 14.0, 8.0).translate((px / 2.0 - 1.0, 0, pt + 4.0)))

    # 4x M3 standoff holes at corners to bolt the bracket to the trunk floor.
    hole_r = clearance_hole("M3") / 2.0
    for bx in (-px / 2.0 + 5.0, px / 2.0 - 5.0):
        for by in (-py / 2.0 + 4.0, py / 2.0 - 4.0):
            plate = plate.cut(cq.Workplane("XY").cylinder(pt + 4.0, hole_r).translate((bx, by, pt / 2.0)))

    return plate.val()
