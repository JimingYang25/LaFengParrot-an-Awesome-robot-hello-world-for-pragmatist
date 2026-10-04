"""Generic 5 V / 3 A BEC step-down module.

Dims from dims/dimensions.json key "bec_5v3a" (all [EST] generic module).
Board 30x20x10 mm, ~100 mm leads (modelled as short stubs here), 15 g.
"""
import cadquery as cq

META = {
    "part_id": "bec_5v3a",
    "name": "5V/3A BEC step-down module",
    "bom_line": "BOM §7 #5 (generic BEC)",
    "qty": 1,
    "mass_g": 15.0,
    "material": "PCB / electronic",
    "source_url": "n/a (generic module, BOM §7 #5)",
    "origin_note": (
        "local frame: origin at module box centre, +X toward the output leads. "
        "Board 30x20x10 = [EST] generic size; leads modelled as 30 mm stubs (real ~100mm)."
    ),
    "print_note": "purchased module — not printed",
}

SIZE = [30.0, 20.0, 10.0]                          # [EST]
STUB = 30.0                                        # stub length (real lead ~100mm)


def build(cfg=None):
    l, w, h = SIZE
    box = cq.Workplane("XY").box(l, w, h)
    # input lead at -X, output lead at +X (workplane YZ -> cylinder axis = X)
    lead_in = (
        cq.Workplane("YZ").cylinder(STUB, 0.8)
        .translate((-l / 2.0 - STUB / 2.0 + 1.0, 0.0, 0.0))
    )
    lead_out = (
        cq.Workplane("YZ").cylinder(STUB, 0.8)
        .translate((l / 2.0 + STUB / 2.0 - 1.0, 0.0, 0.0))
    )
    return box.union(lead_in).union(lead_out).val()
