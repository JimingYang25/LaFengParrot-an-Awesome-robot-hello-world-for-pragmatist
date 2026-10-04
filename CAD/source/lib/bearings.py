"""Miniature deep-groove bearings used in the leg/wing joint pockets.

Parameterised by size (dimensions.json: bearing_mr63 / bearing_mr84):
  MR63ZZ : d=3.0  D=6.0  B=2.5   (shielded, verified)
  MR84   : d=4.0  D=8.0  B=2.0   (open; the shielded MR84ZZ is 4x8x3)
Modelled as a thin ring (outer cylinder minus bore), axis = Z, centred on
the joint axis so the assembly agent can mount it coaxial with a shaft.
"""
import cadquery as cq

META = {
    "part_id": "bearing_mr63",
    "name": "Miniature bearing MR63ZZ / MR84 (parameterised ring)",
    "bom_line": "BOM §6 #16 (MR63ZZ + MR84 joint bearings)",
    "qty": 0,  # parametric; qty set by the joint pockets
    "mass_g": 0.7,
    "material": "chrome steel",
    "source_url": "https://www.ktbearing.com/product/deep-groove-ball-bearing/deep-groove-ball-bearing-mr-series/",
    "origin_note": (
        "local frame: ring centred at origin, axis +Z (joint axis), width B along Z. "
        "build() default = MR63ZZ (d3/D6/B2.5); build(cfg={'size':'MR84'}) = open MR84 "
        "(d4/D8/B2.0). Both sizes verified from bearing tables."
    ),
    "print_note": "purchased bearing — not printed",
}

SIZES = {
    "MR63": {"d": 3.0, "D": 6.0, "B": 2.5},
    "MR63ZZ": {"d": 3.0, "D": 6.0, "B": 2.5},
    "MR84": {"d": 4.0, "D": 8.0, "B": 2.0},
}


def build(cfg=None):
    cfg = cfg or {}
    size = cfg.get("size", "MR63")
    spec = SIZES[size]
    outer = cq.Workplane("XY").cylinder(spec["B"], spec["D"] / 2.0)
    bore = cq.Workplane("XY").cylinder(spec["B"] + 1.0, spec["d"] / 2.0)
    return outer.cut(bore).val()
