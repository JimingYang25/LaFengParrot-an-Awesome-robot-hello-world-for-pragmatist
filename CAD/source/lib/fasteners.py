"""Fasteners library — pattern exemplar for the part-module API (CONVENTIONS §3).

Standard socket-head cap screws (DIN 912 / ISO 4762) + clearance-hole helper.
All dims from the ISO 4762 standard table (source below); no dimensions.json
dependency (CONVENTIONS §4 allows standard parts here).
"""
import cadquery as cq

META = {
    "part_id": "fastener_m2",
    "name": "M2 socket-head cap screw (ISO 4762)",
    "bom_line": "BOM §6 #17 (M2/M2.5/M3 kit)",
    "qty": 0,  # parametric; qty set by assembly fastener list
    "mass_g": 0.3,
    "material": "304 stainless steel",
    "source_url": "https://www.boltdepot.com/fastener-information/printable-tools/iso-socket-head-cap-screw-dimensions",
    "origin_note": "local frame: +Z along screw axis, head at +Z end, shank tip at -Z",
    "print_note": "purchased hardware — not printed",
}

# ISO 4762 socket-head cap screw: head diameter (d_k), head height (k),
# nominal thread diameter (d), hex socket size (s). Values in mm.
ISO4762 = {
    "M2":  {"head_d": 3.8, "head_h": 2.0, "thread_d": 2.0, "socket": 1.5, "clear": 2.2},
    "M2.5": {"head_d": 4.5, "head_h": 2.5, "thread_d": 2.5, "socket": 2.0, "clear": 2.7},
    "M3":  {"head_d": 5.5, "head_h": 3.0, "thread_d": 3.0, "socket": 2.5, "clear": 3.2},
}


def build(cfg=None):
    """Screw as two cylinders (head + shank); chamfer on shank tip.

    cfg: {"size": "M2", "length": 6.0, "smooth": True}
    """
    cfg = cfg or {}
    size = cfg.get("size", "M2")
    length = cfg.get("length", 6.0)
    spec = ISO4762[size]
    smooth = cfg.get("smooth", True)

    shank = cq.Workplane("XY").cylinder(length, spec["thread_d"] / 2.0)
    head = cq.Workplane("XY").workplane(offset=length - 0.05).cylinder(
        spec["head_h"], spec["head_d"] / 2.0
    )
    # hex socket pocket in head (cosmetic; simplified as hexagon)
    if smooth:
        socket = (
            cq.Workplane("XY")
            .workplane(offset=length + spec["head_h"] - 0.1)
            .polygon(6, spec["socket"] * 1.15)
            .extrude(-0.9)
        )
        return shank.union(head).cut(socket).val()
    return shank.union(head).val()


def clearance_hole(size="M2"):
    """Diameter for a clearance hole for a screw of `size` (ISO 273 / common table)."""
    return ISO4762[size]["clear"]


def boss_od(size="M2", wall=2.0):
    """Recommended printed screw-boss outer diameter (CONVENTIONS §5)."""
    return ISO4762[size]["head_d"] + 2.0 * wall
