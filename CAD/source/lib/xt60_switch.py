"""XT60 in-line power switch + connector pair.

Dims from dims/dimensions.json key "xt60_switch" (all [EST]): two standard
XT60 housings (17.5x21.5x14) joined to an inline toggle switch body
(50x25x20). This module covers the XT60 connectors in the power chain, so
the optional standalone xt60_connector.py is NOT written.
"""
import cadquery as cq

META = {
    "part_id": "xt60_switch",
    "name": "XT60 in-line power switch (male+female pair)",
    "bom_line": "BOM §7 #3 (XT60 on/off switch)",
    "qty": 1,
    "mass_g": 30.0,
    "material": "plastic / copper contacts",
    "source_url": "n/a (standard XT60 + generic inline switch)",
    "origin_note": (
        "local frame: origin at switch-body centre, inline axis along +X. "
        "Switch body 50x25x20 at centre; XT60 housings (17.5x21.5x14) at +/-X ends. "
        "All dims [EST] (standard XT60 + generic inline switch listing)."
    ),
    "print_note": "purchased hardware — not printed",
}

SWITCH = [50.0, 25.0, 20.0]                        # [EST]
XT60 = [17.5, 21.5, 14.0]                          # [EST] standard housing


def build(cfg=None):
    sl, sw, sh = SWITCH
    xl, xw, xh = XT60
    body = cq.Workplane("XY").box(sl, sw, sh)

    # toggle rocker nub on top
    toggle = (
        cq.Workplane("XY")
        .box(8.0, 6.0, 4.0)
        .translate((0.0, 0.0, sh / 2.0 + 2.0))
    )

    left = (
        cq.Workplane("XY")
        .box(xl, xw, xh)
        .translate((-(sl / 2.0 + xl / 2.0 - 0.5), 0.0, 0.0))
    )
    right = (
        cq.Workplane("XY")
        .box(xl, xw, xh)
        .translate((+(sl / 2.0 + xl / 2.0 - 0.5), 0.0, 0.0))
    )
    return body.union(toggle).union(left).union(right).val()
