"""3S 11.1 V 2200 mAh LiPo pack (XT60).

Dims from dims/dimensions.json key "lipo_3s_2200". Pack 105x34.5x26 mm,
185 g. XT60 discharge lead stub at +X end; JST-XH 4-pin balance stub at the
other end (thin rectangular prisms).
"""
import cadquery as cq

META = {
    "part_id": "lipo_3s_2200",
    "name": "3S 11.1V 2200mAh LiPo pack (XT60)",
    "bom_line": "BOM §2 #2 (3S 2200mAh LiPo)",
    "qty": 1,
    "mass_g": 185.0,
    "material": "LiPo pouch",
    "source_url": "https://zeeebattery.com/products/zeee-3s-lipo-battery-2200mah-11-1v-120c-xt60",
    "origin_note": (
        "local frame: origin at pack box centre, +X toward the XT60 end. "
        "Pack box z centred (thickness 26). XT60 stub at +X, JST-XH balance stub at -X. "
        "Pack dims 105x34.5x26 and 185g = verified listing; connector housings simplified."
    ),
    "print_note": "purchased battery — not printed; lowest in CoM stack",
}

SIZE = [105.0, 34.5, 26.0]                        # verified


def build(cfg=None):
    l, w, h = SIZE
    pack = cq.Workplane("XY").box(l, w, h)

    # XT60 plug stub at +X end (face already touches the pack box at x=+l/2)
    xt60 = (
        cq.Workplane("XY")
        .box(17.5, 14.0, 14.0)
        .translate((l / 2.0 + 8.75 - 0.5, 0.0, 0.0))
    )
    # JST-XH 4-pin balance stub at -X end
    balance = (
        cq.Workplane("XY")
        .box(8.0, 6.0, 4.0)
        .translate((-l / 2.0 - 4.0 + 0.5, 0.0, 0.0))
    )

    return pack.union(xt60).union(balance).val()
