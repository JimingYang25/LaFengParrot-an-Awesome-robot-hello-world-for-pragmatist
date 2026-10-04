"""5x20 mm glass fuse + in-line holder.

Dims from dims/dimensions.json key "fuse_holder". Fuse itself O5x20 mm
(standard, verified); holder body 30x15x10 mm [EST].
"""
import cadquery as cq

META = {
    "part_id": "fuse_holder",
    "name": "5x20mm fuse + in-line holder",
    "bom_line": "BOM §7 #4 (in-line fuse holder)",
    "qty": 1,
    "mass_g": 10.0,
    "material": "glass fuse / plastic holder",
    "source_url": "n/a (standard 5x20mm fuse + generic holder)",
    "origin_note": (
        "local frame: origin at holder centre, fuse axis along +X. "
        "Fuse O5x20 = standard/verified; holder body 30x15x10 = [EST] generic inline holder."
    ),
    "print_note": "purchased hardware — not printed",
}

FUSE_D, FUSE_L = 5.0, 20.0                         # standard
HOLDER = [30.0, 15.0, 10.0]                        # [EST]


def build(cfg=None):
    hl, hw, hh = HOLDER
    holder = cq.Workplane("XY").box(hl, hw, hh)
    # fuse glass tube along X (workplane YZ -> axis = X)
    fuse = (
        cq.Workplane("YZ").cylinder(FUSE_L, FUSE_D / 2.0)
        .translate((0.0, 0.0, 0.0))
    )
    # flying leads +/-X
    lead_l = (
        cq.Workplane("YZ").cylinder(15.0, 0.8)
        .translate((-(hl / 2.0 + 7.5 - 1.0), 0.0, 0.0))
    )
    lead_r = (
        cq.Workplane("YZ").cylinder(15.0, 0.8)
        .translate((+(hl / 2.0 + 7.5 - 1.0), 0.0, 0.0))
    )
    return holder.union(fuse).union(lead_l).union(lead_r).val()
