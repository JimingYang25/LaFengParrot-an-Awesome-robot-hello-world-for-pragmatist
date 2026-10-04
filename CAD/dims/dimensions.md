# LaFengParrot CAD — Hardware Mechanical Dimensions

Build variant: **all-Feetech** — legs 6× ST-3215-C018 (12 V, 30 kg·cm), wings/neck 4× SC-0043-C001.
Units: mm (mass g). Research date 2026-09-27.

**Legend:** ✅ verified = read from a datasheet / product page this session. ⚠ [EST] = estimated; see the register at the end for the basis.

---

## 1. Feetech ST-3215-C018 (leg servos, ×6)

Source: official datasheet PDF https://www.feetech.cn/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf ; outline drawing https://www.feetechrc.com/en/525603.html

| Dimension | Value (mm) | Verified? | Source | Notes |
|---|---|---|---|---|
| Body L × W × H | 45.2 × 24.7 × 35.0 | ✅ | datasheet §6-1 | "45.2X24.7X35" |
| Mount holes (output face) | 4× at (6.5,2.5)/(27.2,2.5)/(6.5,22.2)/(27.2,22.2) | ⚠ [EST] | measured off drawing Fig.9 | drawing does not label hole coords; pocket dim = body box |
| Mount hole Ø / screw | Ø2.2 / M2 (PA2.0 self-tap) | ⚠ [EST] | drawing "B-PA2.0自攻螺丝" | 4 corner PA2.0 case screws at ~(1.7,1.1)/(43.5,1.1)/(1.7,23.6)/(43.5,23.6) are case fasteners |
| Output shaft spline | 25T | ✅ | datasheet §6-9 | "25T/OD5.9mm" |
| Output shaft O/D | 5.9 | ✅ | datasheet §6-9 | |
| Output shaft length | ~6.0 | ⚠ [EST] | horn section X-X | dual-shaft (双轴); rear plain bore ~Ø6 opposite face |
| Axis direction | normal to 45.2×24.7 face | ✅ | drawing | |
| Horn: flange O/D | 19.95 (~20) | ✅ | horn drawing | octagonal flange |
| Horn: hub bore | 25T / Ø5.9 | ✅ | horn drawing "25T(5.9铜齿)" | |
| Horn: arm / bracket screws | 4× M3 (on ~Ø14 BCD) + 4× Ø3.2 clearance (~Ø9 BCD) | ✅ | horn drawing "4-M3" / "Ø3.2" | |
| Horn retaining screw | M3×6 | ✅ | datasheet §6-13 "M3X6机牙螺丝" | |
| Horn thickness | flange 2.5 / hub 4.5 | ✅ | horn section X-X | |
| Connector | 5264-3P, 2.54 pitch, 3-pin (GND/Vcc/SIG), 15 cm cable | ✅ | datasheet §6-7 | on bottom face opposite shaft |
| Mass | 55 g (±1) | ✅ | datasheet §6-8 | |

---

## 2. Feetech SC-0043-C001 (wings/neck servos, ×4)

Source: product page https://www.feetech.cn/en/559569

| Dimension | Value (mm) | Verified? | Source | Notes |
|---|---|---|---|---|
| Body L × W × H | 20.3 × 8.5 × 19.39 | ✅ | product page "A:20.3 B:8.5 C:19.39" | |
| Mount holes | 2 ears, Ø~2.0, center spacing 20.3 | ⚠ [EST] | outline drawing | bottom view dims 27.35 outer / 23.6 body / 20.3 hole spacing |
| Mount screw | M2 | ⚠ [EST] | drawing "Φ2" ear holes | |
| Output shaft spline | 28T | ✅ | product page "28T/Φ3.9mm" | |
| Output shaft O/D | 3.9 | ✅ | product page | |
| Output shaft protrusion | 3.1 | ✅ | side view "3.1" | |
| Horn retaining screw | M1.7 | ✅ | drawing "28T-M1.7" | |
| Stock horn arm span | ~15 | ⚠ [EST] | typical 4.3 g servo horn | |
| Connector | 3-pin bus, 15 cm cable | ✅ | product page "Connector wire: 15cm" | exact JST family not published |
| Mass | 6.6 g (±0.5) | ✅ | product page | |

---

## 3. Jetson Orin Nano Super dev-kit reference carrier + stock cooler

Source: NVIDIA Carrier Board Spec SP-11324-001 https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf (Fig 4-1, Fig 4-2)

Coordinate system: origin = top-left of the 100×79 PCB, +X right, +Y down (mm).

| Dimension | Value | Verified? | Source | Notes |
|---|---|---|---|---|
| Overall envelope (w/ cooler+feet) | 103.0 × 90.5 × 34.77 mm | ✅ | Fig 4-2 | 103±0.2 / 90.5±0.2 / 34.77±1.09 |
| PCB size | 100.0 × 79.0 mm | ✅ | Fig 4-1 | 100±0.13 / 79±0.13 |
| PCB thickness | 1.57 mm | ✅ | Fig 4-1 side view | 1.57±0.16 |
| Component height (top side) | 16.70 mm max | ✅ | Fig 4-1 side view | |
| Component height (bottom) | 4.30 mm max | ✅ | Fig 4-1 side view | |
| Mount holes | (4,4)/(96,4)/(4,56)/(96,56) | ⚠ [EST] | measured off Fig 4-1 raster | spec gives no coords; 4 corner plated holes |
| Mount screw | M2.5 | ⚠ [EST] | standard dev-kit standoff | |
| Feet / standoff height | ~5 mm | ⚠ [EST] | BOM §2 CAD note | |
| Connector: DC barrel (J16) | (10, 66) | ⚠ [EST] | Fig 4-1 | barrel 5.5 O/D, 2.5 pin, 9.5 mm long (verified §3.8) |
| Connector: 40-pin header (J12) | (35, 5) | ⚠ [EST] | Fig 4-1 | top edge |
| Connector: CSI #0 (J20) | (3, 21) | ⚠ [EST] | Fig 4-1 | left edge, upper flex connector |
| Connector: CSI #1 (J21) | (3, 40) | ⚠ [EST] | Fig 4-1 | left edge, lower flex connector |
| Connector: microSD slot | (68, 62) | ⚠ [EST] | Fig 4-1 | bottom edge |
| Connector: USB cluster (USB-C J5) | (25, 68) | ⚠ [EST] | Fig 4-1 | USB-A J6/J7 at ~(42,68)/(55,68) |
| Fan exhaust (blows upward off heatsink) | (50, 30) | ⚠ [EST] | Fig 4-2 fan center | |
| SoDIMM module center | (48, 28) | ⚠ [EST] | Fig 4-1 | module sits above long SoDIMM slot |
| Dev-kit assembly mass | 175 g | ✅ | §4 "Developer Kit Weighs 0.175kg" | |

---

## 4. 3S 11.1 V 2200 mAh LiPo (XT60)

Source: Zeee listing https://zeeebattery.com/products/zeee-3s-lipo-battery-2200mah-11-1v-120c-xt60 (cross-checked Gens Ace / HRB / Rhino)

| Dimension | Value | Verified? | Source | Notes |
|---|---|---|---|---|
| Pack L × W × H | 105 × 34.5 × 26 mm | ✅ | Zeee listing | brands vary 105×33–35×19–27; Gens Ace 105×34×23, Rhino 107×35×26.5 |
| Mass | 185 g | ✅ | Zeee listing | |
| Discharge connector | XT60 | ✅ | listing | |
| Balance lead | JST-XH 4-pin | ✅ | listings | exits same end as XT60 |

---

## 5. 5 V / 3 A BEC module

| Dimension | Value | Verified? | Source | Notes |
|---|---|---|---|---|
| Board L × W × H | 30 × 20 × 10 mm | ⚠ [EST] | generic | small 2-side buck PCB; exact size varies by brand |
| Wire length | ~100 mm leads | ⚠ [EST] | generic | |
| Mass | 15 g | ⚠ [EST] | BOM §7 | |

---

## 6. XT60 power switch + inline fuse holder

| Dimension | Value | Verified? | Source | Notes |
|---|---|---|---|---|
| XT60 housing | 17.5 × 21.5 × 14 mm | ⚠ [EST] | standard XT60 part | |
| Inline switch body | 50 × 25 × 20 mm | ⚠ [EST] | generic | XT60 leads + rocker toggle |
| Glass fuse | Ø5 × 20 mm | ✅ | standard 5×20 | |
| Fuse holder body | 30 × 15 × 10 mm | ⚠ [EST] | generic inline holder | |

---

## 7. ICM-42688-P IMU breakout

Source: chip datasheet https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf

| Dimension | Value | Verified? | Source | Notes |
|---|---|---|---|---|
| Chip package | 2.5 × 3.0 × 0.91 mm LGA | ✅ | TDK datasheet | the bare IC |
| Breakout PCB | 20 × 20 × 2 mm | ⚠ [EST] | generic GY breakout | 4× M2 holes at corners (2,2)/(18,2)/(2,18)/(18,18), Ø2.2 |
| Mass | 4 g | ⚠ [EST] | BOM §2 | |

---

## 8. Bearings

| Bearing | d (bore) | D (outer) | B (width) | Verified? | Source |
|---|---|---|---|---|---|
| MR63ZZ | 3.0 | 6.0 | 2.5 | ✅ | https://detail.1688.com/offer/570803238776.html |
| MR84 (open) | 4.0 | 8.0 | 2.0 | ✅ | https://www.ktbearing.com/product/deep-groove-ball-bearing/deep-groove-ball-bearing-mr-series/ |

Note: shielded **MR84ZZ** is 4×8×**3** mm; the open MR84 used in the joint pockets is 4×8×2.

---

## 9. Fasteners (DIN 912 / ISO 4762 socket head cap screws)

Source: https://engineeringhardware.com/guide/standard/din-912-socket-head-cap-screws/

| Size | Head Ø dk | Head height k | Thread | Clearance hole | Lengths in BOM | Verified? |
|---|---|---|---|---|---|---|
| M2 | 3.8 | 2.0 | 2.0 | 2.2 | M2×6 | ✅ |
| M2.5 | 4.5 | 2.5 | 2.5 | 2.7 | M2.5×8 | ✅ |
| M3 | 5.5 | 3.0 | 3.0 | 3.2 | M3×10 | ✅ |

---

## Unverifiable / [EST] register

Every number below could NOT be read directly from a datasheet this session and is an estimate. Frame parts consuming these MUST mark them in `META["origin_note"]`.

| # | Item | Estimated value | Basis / method |
|---|---|---|---|
| 1 | ST-3215-C018 mount-hole xy coords | (6.5,2.5)/(27.2,2.5)/(6.5,22.2)/(27.2,22.2) | pixel-measured off the Fig.9 outline raster; drawing labels only body box (45.2×24.7) and shaft. Verify against physical servo. |
| 2 | ST-3215-C018 shaft protrusion length | ~6.0 mm | inferred from horn/hub section (hub 4.5 + spline engagement); not explicitly dimensioned. |
| 3 | SC-0043-C001 mount hole spacing | 20.3 mm | from bottom-view dimension "20.3" on the outline drawing; ear hole Ø~2 inferred (drawing labels Φ2 near shaft). |
| 4 | SC-0043-C001 horn arm span | ~15 mm | typical 4.3 g micro-servo horn; not on drawing. |
| 5 | SC-0043-C001 connector JST family | "3-pin" only | product page says 15 cm wire but not the connector part number. |
| 6 | Orin carrier mount-hole xy | (4,4)/(96,4)/(4,56)/(96,56) | pixel-measured off Fig 4-1 raster; NVIDIA spec gives board outline but no hole coordinates. |
| 7 | Orin carrier all connector xy (barrel/40pin/csi1/csi2/microsd/usb/fan/module center) | per table above | pixel-estimated off Fig 4-1/4-2 raster. |
| 8 | Orin carrier feet height | ~5 mm | BOM §2 packing note; not in SP-11324. |
| 9 | Orin carrier mount screw size | M2.5 | standard dev-kit standoff; not explicitly stated. |
| 10 | BEC 5V3A board size / wires / mass | 30×20×10 mm, 100 mm leads, 15 g | generic small buck module; BOM lists it as a generic item. |
| 11 | XT60 housing size | 17.5×21.5×14 mm | standard XT60 (not re-verified from a datasheet this session). |
| 12 | XT60 switch body size | 50×25×20 mm | generic inline switch listing. |
| 13 | Fuse holder body size | 30×15×10 mm | generic 5×20 inline holder. |
| 14 | ICM-42688-P breakout PCB size / holes | 20×20×2 mm, 4×M2 corners | generic GY breakout; only the bare chip (2.5×3×0.91) is datasheet-verified. |

No values were fabricated: every servo dimension the frame needs (body box, mount holes, shaft, horn) is present, every carrier connector coordinate is present (flagged [EST] where estimated), and every row carries either a verified source URL or an explicit [EST] basis.
