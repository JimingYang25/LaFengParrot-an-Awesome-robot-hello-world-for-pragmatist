# LaFengParrot — ASSEMBLY.md (part tree ↔ BOM, dimensions, fasteners, cables, joints)

Frozen build variant: **all-Feetech** (pinned, BOM §7). Legs 6× ST-3215-C018
(12 V, 30 kg·cm), wings/neck 4× SC-0043-C001, one FT-SCS TTL bus, one 3S pack.
Global frame: **+X beak/forward, +Y parrot-left, +Z up**; origin on the sagittal
plane at the two hip_roll output axes (the "hip plane", z=0). Units mm, masses g.

Placement authority: `source/assembly/ASSEMBLY_REPORT.md` §2 (**REV-B stability
rebuild**, 2026-09-27; repository path `CAD/`). Dimensions authority:
`dims/dimensions.md` (+ `dimensions.json`). Kinematic contract: `CONVENTIONS.md` §6.
Nothing here is invented; every number traces to one of those three files or a
BOM.md row. REV-B anchors: 54 mm hip rail, 40×44 feet (10 mm inner gap), neck
pitch axis z=185, carrier board-top z=72, total height 394 mm.

---

## 1. Part tree ↔ BOM mapping (1:1)

19 registry part_ids (the purchased fasteners/bearings are parameterized solids,
not printed). Frame prints → BOM §2 #9 mass line + §6 #16 PETG filament; hardware
solids → their §2/§6/§7 rows. "mounted qty" is the count baked into the standing
assembly (`poses._INSTANCES`, 29 instances over 19 part types).

| part_id (registry) | name | mounted qty | material | mass_g (CAD META) | BOM mass line | BOM purchase line |
|---|---|---|---|---|---|---|
| **Servos (FT-SCS bus)** |||||||
| `st3215_c018` | ST-3215-C018 leg servo (25T) | 6 | Al gearbox / case | 55 ea (330) | §2 #3-equivalent → §7 variant table (legs) | **§7 costed #1** (6×, ¥118.50, 1688 spot) |
| `sc0043_c001` | SC-0043-C001 wing/neck servo (28T) | 4 | plastic/metal gear | 6.6 ea (26.4) | §2 #4-equivalent → §7 variant | **§7 costed #2** (4×, ¥55 [EST]) |
| — spares (C018×1 + SC-0043×1, not mounted) | | 2 | | 0 mounted | — | **§7 costed #3** (174 [EST]) |
| **Compute / electronics** |||||||
| `orin_carrier` | Orin Nano Super dev-kit reference carrier + stock cooler + feet | 1 | PCB / Al heatsink / fan | 175 (assembly; §2 splits 15 g module #1 + 160 g board #2) | **§2 #1 + #2** | **§6 #1** (owned, ¥0; JD 10149183026930) |
| `lipo_3s_2200` | 3S 11.1 V 2200 mAh LiPo (XT60) | 1 | LiPo pouch | 185 | **§2 #7** (185 g, listing) | **§6 #11** (×2 incl. spare) |
| `bec_5v3a` | 5 V/3 A BEC (wings/neck rail) | 1 | PCB buck | 15 [EST] | §2 #6-equivalent (small 5 V buck) | **§7 costed #5** (¥20 [EST], 15 g) |
| `xt60_switch` | XT60 in-line power switch (M+F) | 1 | plastic/Cu | 30 | **§2 #8** (switch+fuse set, 30 g) | **§6 #13** (XT60 switch + 10 A fuse + holder) |
| `fuse_holder` | 5×20 mm glass fuse + in-line holder | 1 | glass/plastic | 10 | **§2 #8** (same set) | **§6 #13** (same set) |
| `imuc_icm42688p` | ICM-42688-P IMU breakout (20×20) | 1 | PCB/LGA | 4 [EST] | **§2 #11** (4 g) | **§6 #14** |
| **Frame prints (PETG FDM)** |||||||
| `trunk_shell` | Trunk shell (split upper/lower) | 1 | PETG | 230 ⚠ | **§2 #9** (PETG frame 230 g [EST] roll-up) | **§6 #16** (PETG 1 kg) |
| `hip_mount` | Hip-roll servo mount (L/R) | 2 | PETG | 42 ea | **§2 #9** | §6 #16 |
| `thigh_link` | Thigh link (2× C018 pocket) | 2 | PETG | 55 ea | **§2 #9** | §6 #16 |
| `shin_link` | Shin link w/ integrated fixed rocker sole | 2 | PETG | ≈18.8 ea CAD (20.2 incl. lump) | **§2 #9** | §6 #16 |
| `wing_arm` | Wing arm + printed panel (L/R) | 2 | PETG | 14 ea | **§2 #9** | §6 #16 |
| `neck_linkage` | Neck yaw+pitch bracket (2× SC-0043) | 1 | PETG | 30 | **§2 #9** | §6 #16 |
| `head_shell` | Parrot head shell (hollow) | 1 | PETG | 40 | **§2 #9** | §6 #16 |
| `battery_tray` | LiPo cradle tray | 1 | PETG | 35 | **§2 #9** | §6 #16 |
| `power_mount` | BEC / XT60 / fuse bracket | 1 | PETG | 28 | **§2 #9** | §6 #16 |
| **Purchased hardware (parameterized solids)** |||||||
| `fastener_m2` (M2.5/M3 kit) | ISO 4762 SHCS — M2/M2.5/M3 | set | 304 SS | 0.3 ea | **§2 #10** (fasteners + horns + bearings 60 g) | **§6 #17** (M2/M2.5/M3 304 kit) |
| `bearing_mr63` | MR63ZZ (3×6×2.5) / MR84 (4×8×2) | ~25 | chrome steel | 0.7 ea | **§2 #10** | **§6 #18** (MR63/MR84 ~25 pc) |

**Board-level (not a printed part_id, but on the robot):** SN74LVC1G126 bus
transceiver ×5 → **§6 #8 / §7 costed #6**; Feetech 3-pin bus cables ~10 pc →
**§7 costed #4**; wiring/sleeving/2200 µF bulk cap → **§2 #12** (45 g) +
**§6 #20** sleeving. Bench-only (not mounted): Feetech URT-1 adapter →
**§6 #9 / §7 costed #7**; 格氏 B3 charger → §6 #12.

> ⚠ **Mass reconciliation flag (not invented):** the CAD per-part frame masses
> (trunk 230 + hip 84 + thigh 110 + shin 52 + wing 28 + neck 30 + head 40 +
> tray 35 + power 28 ≈ **637 g**) sum well above BOM §2 #9's 230 g, which was
> the original duck-class estimate. The 230 g on `trunk_shell.META` appears to
> be that whole-frame figure carried onto one part. Next mass roll-up should
> replace §2 #9 with the summed CAD masses; robot total then lands above the
> 1.15 kg Feetech target (re-run the §1 torque margin, which scales ∝ M).

> ⚠ **META `bom_line` strings are stale:** several modules carry e.g.
> `bom_line="§2 #12"`/`"#13"`/`"#17"` that reference an older per-part mass table
> (the current BOM §2 ends at row #12). This table is authoritative; treat the
> in-code strings as deprecated.

---

## 2. Dimension table (sources: dimensions.md + ASSEMBLY_REPORT.md)

| Dimension | Value | Source | Verified? |
|---|---|---|---|
| Standing envelope x | [−64.0, +72.0] mm | REPORT §1 | measured STEP (XT60 switch/lead hardware; no 150 mm cable extremes) |
| Standing envelope y | [−190.9, +190.9] mm | REPORT §1 | measured (wing panel rounded tips) |
| Standing envelope z | [−138.0, +256.1] mm | REPORT §1 | measured (sole floor −138 → crest +256) |
| **Total structural height** | **394 mm** | REPORT §1 | −138 → +256.1 |
| Hip half-spacing / rail | 27 mm / **54 mm** | REPORT §2 (CONVENTIONS §6 nominal 52) | L/R hip_roll axes at y=±27 |
| Thigh link (hip_pitch → knee) | 42 mm | CONVENTIONS §6 / poses | placement z 0→−42 |
| Shin link (knee → sole) | 50 mm | CONVENTIONS §6 / poses | placement z −84→−134 |
| Leg drop (hip plane → foot) | 138 mm | REPORT §1 | z 0 → −138 |
| Foot sole | **40 (X) × 44 (Y) mm** compound rocker, 32 mm flat centre, 10 mm inner gap | REPORT §3 | symmetric 4 mm faceted toe/heel zones; fixed to shin, no wheel; L sole y[5,49], R y[−49,−5] |
| Trunk floor underside | z = 33 mm | REPORT §2 | trunk_shell placed (0,0,+33) |
| Trunk roof | z = 133 mm | REPORT §2 | trunk height = 100 mm |
| Carrier board-top | z = 72 mm | REPORT §2/§4 | orin_carrier placed (0,0,+72) |
| Carrier cooler exhaust top | z = 100 mm | REPORT §4 | roof vent z 128.5–133.5; ~28 mm plenum |
| Carrier standoff height | **33 mm [EST]** | REPORT §8 | feet bottom z=65.4 above trunk floor 33; verify printed bosses |
| Neck linkage base | z = 133 mm | REPORT §2 | neck_linkage placed (0,0,+133) |
| Neck pitch axis | z = 185 mm | REPORT §2 | linkage local z=52; head_shell placed (0,0,+185) |
| Head crest | z = 256 mm | REPORT §1 | measured (tilted crest fins) |
| Wing shoulder / panel tip | y = ±62 / ±190.9 mm | REPORT §2/§1 | span ≈ 382 mm |
| Battery pack | (0, −23, +49), box z 36–62 | REPORT §2 | low, CoM; clears carrier feet 64 by 2 mm |
| Power bracket Y | y = +23 | REPORT §2 | power_mount placed (0,+23,+36) |
| ST-3215-C018 body box | 45.2 × 24.7 × 35.0 mm | dims §1 | ✅ datasheet |
| C018 shaft / horn screw | 25T, Ø5.9 / **M3×6** | dims §1 | ✅ datasheet §6-9/§6-13 |
| SC-0043 body box | 20.3 × 8.5 × 19.39 mm | dims §2 | ✅ product page |
| SC-0043 horn screw | **M1.7** (28T, Ø3.9) | dims §2 | ✅ drawing |
| Orin carrier envelope | 103 × 90.5 × 34.77 mm | dims §3 | ✅ SP-11324 Fig 4-2 |
| LiPo pack | 105 × 34.5 × 26 mm, 185 g | dims §4 | ✅ listing |
| Bearings | MR63ZZ 3×6×2.5; MR84 4×8×2 (open) | dims §8 | ✅ |
| Fastener head/thread | M2 (Ø3.8), M2.5 (Ø4.5), M3 (Ø5.5) | dims §9 | ✅ DIN 912 |

---

## 3. Fastener list (derived from dimensions.md hole patterns)

Counts are nominal from the hardware hole layouts; final counts are confirmed at
first assembly. Screw-boss mapping: printed PETG bosses self-tap M2 (bore
thread+0.1 per CONVENTIONS §5); carrier uses M2.5 standoffs.

| Joint / assembly | Fastener | Qty (nominal) | Source |
|---|---|---|---|
| Each C018 leg servo in its pocket (hip_mount, thigh_link) | M2 / PA2.0 self-tap (Ø2.2 hole) | 4 per servo × 6 = 24 | dims §1 (4 corner PA2.0) |
| Each C018 horn → link retention | **M3×6** | 1 per servo × 6 = 6 | dims §1 "M3X6机牙" |
| C018 horn arm-to-link bracket | M3 (Ø3.2 clearance) | ~4 per horn × 6 = 24 | dims §1 "4-M3 / Ø3.2" |
| Each SC-0043 ear mount (wing shoulder, neck) | M2 (Ø2.0 ear hole) | 2 per servo × 4 = 8 | dims §2 |
| Each SC-0043 horn retention | **M1.7** | 1 per servo × 4 = 4 | dims §2 "28T-M1.7" |
| Orin carrier → trunk standoffs | M2.5×8 (4 corners) | 4 | dims §3 (M2.5, 4 plated holes) |
| IMU breakout → head pocket | M2 (4 corners) | 4 | dims §7 (4×M2 corners) |
| Joint pivot bearings | MR63ZZ (hip roll bore d=3) / MR84 (pitch/knee bore d=4) | ~25 total | dims §8, §6 #18 |
| Trunk upper/lower shell bolt-up, tray/power bracket bosses | M2 self-tap | per print_note | CONVENTIONS §5 |

---

## 4. Cable routing

**Power (one 3S pack, two rails):**
```
3S 11.1 V 2200 mAh (XT60, y=−23, low CoM)
 └─ 10 A in-line fuse (fuse_holder) → XT60 switch (xt60_switch, y=+23)
     ├─→ reference carrier barrel (9–20 V): Orin rail (board-top z=72)
     ├─→ LEG servos C018 ×6: 3S DIRECT (4.0–14 V rated; no leg buck)
     └─→ 5 V/3 A BEC (bec_5v3a) → WING/NECK servos SC-0043 ×4 (3.7–6 V max)
```
Legs take 11.1 V straight off the pack; only the small wings/neck segment goes
through the 5 V BEC (BOM §7 power section). Bulk cap 2200 µF low-ESR at the
first servo node; chains ≤60 cm, 22 AWG. Service ports per REPORT §4 (microSD
+Y, barrel +Y, USB +Y, 40-pin −Y, fan exhaust +Z, XT60 +X corner) are all open.

**Signal (one half-duplex FT-SCS TTL bus):**
```
carrier 40-pin header UART1 (pin8 TX / pin10 RX, 3.3 V)
  → SN74LVC1G126 tri-state buffer (free GPIO = bus direction: HIGH tx / LOW rx)
  → single 3-pin DATA chain: leg chain → wing/neck chain
```
- **Power taps on the same SIG+GND chain:** leg segment fed at 3S, wing/neck
  segment fed at 5 V (pin 2 Vcc breaks at the rail boundary); SIG+GND continuous
  end-to-end (BOM §7 "one bus, one SDK").
- **Baud 115200–500 kbps:** SC-0043 caps at 500 kbps; re-flash C018 down from
  its 1 Mbps default. 500 kbps preferred → 10-servo sync cycle ≈ 3–4 ms, inside
  the 20 ms / 50 Hz loop budget.
- Fallback if power-split signal integrity fails on the bench: two buses
  (2× UART + 2× transceiver, rails cleanly separated) — BOM §7 note.

---

## 5. Joint axes & zero poses (for the future MuJoCo model)

Zero pose = **standing** (trunk vertical, legs straight down z, wings level ±Y,
neck straight up). The crouched gait (hip_pitch 26°/knee ~0°) is a *policy*
offset, NOT the CAD zero — record both. All 10 joints, axis direction ∥ global
axis, position = output-axis origin in the global frame:

| # | joint | axis ∥ | position (x, y, z) mm | servo (instance) |
|---|---|---|---|---|
| 1 | hip_roll L | **X** | (0, +27, 0) | st3215_hiproll_L |
| 2 | hip_roll R | **X** | (0, −27, 0) | st3215_hiproll_R |
| 3 | hip_pitch L | **Y** | (0, +44.5, −42) | st3215_hippitch_L |
| 4 | hip_pitch R | **Y** | (0, −44.5, −42) | st3215_hippitch_R |
| 5 | knee_pitch L | **Y** | (0, +44.5, −84) | st3215_knee_L |
| 6 | knee_pitch R | **Y** | (0, −44.5, −84) | st3215_knee_R |
| 7 | wing_flap L | **Y** | (0, +71.7, +60) | sc0043_wing_L |
| 8 | wing_flap R | **Y** | (0, −71.7, +60) | sc0043_wing_R |
| 9 | neck_yaw | **Z** | (0, 0, +155.39) | sc0043_neckyaw |
| 10 | neck_pitch | **Y** | (0, +9.7, +185) | sc0043_neckpitch |

These REV-B positions are the **MuJoCo-inherited contract**: rebuild the MJCF at
these exact output-axis origins and zero angles; do not reuse REV-A z=203.

**Hip-rail deviation to carry into MuJoCo:** L/R hip_roll axes are **54 mm
apart (±27 mm)**, widened from the CONVENTIONS §6 nominal 52 mm and far wider
than microduck's **34 mm (±17 mm)** — the C018 body (45.2×24.7×35, 55 g) makes
the hip_mount housing 50.6 mm wide in Y, which overlaps across the sagittal
plane at ±17. MuJoCo kinematics MUST use 54 mm.

**Torque re-check reference (REPORT §6, REV-B):** lever r = 33 mm, required
@2× safety = 0.647·M. At the real built mass **M = 1.485 kg** (frame+hardware
1.38 kg + 105 g lump): required = **0.961 N·m** vs C018 stall ≈ 2.72 N·m @11.1 V
→ **margin 2.83× (PASS)**. Without lump (M = 1.38 kg): required 0.893 N·m →
3.05×. (REV-A's 3.65× was the lighter 1.15 kg estimate; the REV-B baked-centroid
mass supersedes it.)

---

## 6. Print & assembly notes

- **Material PETG FDM** (BOM §6 #16 PolyLite/金质). Structural walls ≥2.0 mm,
  servo pockets ≥1.6 mm, shell 1.6 mm (CONVENTIONS §5). Corner radii ≥1 mm.
- `trunk_shell`: split horizontally at local Z=50 into upper (roof + vent slots)
  and lower — bed-size split **finalized when the user's printer bed is known**
  (CONVENTIONS §5 / BOM §9: Ender-3 220 mm vs Bambu 256 mm).
- `hip_mount`: print with output axis (X) horizontal; ±X bearing bore faces away
  from supports for dimensional cleanliness.
- `thigh_link`: print on edge (beam vertical) so the two Y-axis bores are clean.
- `shin_link`: print on one 40×62 mm side so the rocker profile lies in the bed plane; 4 perimeters, 35% gyroid PETG, knee bore horizontal, no support.
- `wing_arm`: panel flat on bed (thin Z), shoulder pocket on edge.
- `neck_linkage`: base flat, yoke on edge; 2 mm walls; yaw bore clean.
- `head_shell`: print upside-down (skull crown on bed) so beak/crest need no supports.
- **Tray seating (REV-B):** `battery_tray` base underside now sits on the trunk
  floor (z=33); pack box z 36–62 clears the carrier feet (bottom z≈65.4) by 2 mm.
  The prior REV-A tray-vs-feet nick is resolved (REPORT §8) — no further trim needed.
- Designed contacts are expected (servos in pockets, horn/pivot mates, tray/pack,
  power devices in channels); REV-B keeps only 15 mm cosmetic cable stubs and
  BEC/fuse fly-leads that may lightly touch (benign, REPORT §3) — dress/sleeve them.

---

## 7. [EST] register & next-revision items

**[EST] values consumed by the frame (from dimensions.md register):**
1. C018 mount-hole xy coords — pixel-measured off Fig.9 (verify against physical servo).
2. C018 shaft protrusion ~6.0 mm.
3. SC-0043 mount-hole spacing 20.3 mm / ear Ø~2.
4. SC-0043 horn arm span ~15 mm.
5. SC-0043 connector JST family ("3-pin" only).
6. Orin carrier mount-hole xy + all connector xy (pixel-estimated off SP-11324).
7. Orin carrier feet/standoff height (~5 mm stock feet; the on-robot **33 mm**
   trunk standoffs are a printed-boss estimate, REPORT §8).
8. Orin carrier mount screw M2.5 (standard standoff).
9. BEC 5V3A board 30×20×10 mm / 100 mm leads / 15 g.
10. XT60 housing / switch body / fuse-holder body sizes (generic).
11. ICM-42688-P breakout PCB 20×20 / 4×M2 corners (only the bare IC is datasheet-verified).

**Next-revision backlog:**
- **Carrier standoff height 33 mm [EST]** — verify against printed trunk bosses;
  REV-B value = feet bottom z=65.4 above trunk floor z=33 (REPORT §8).
- **Power-device lead routing** — BEC/fuse/XT60 fly-leads may lightly touch
  channels (REPORT §3 cosmetic); route/sleeve at final assembly.
- **Frame mass roll-up** — the REV-B baked-centroid mass (1.38 kg frame+hardware,
  1.485 kg with lump) supersedes both the BOM §2 #9 (230 g) and the old per-part
  META sum; reconcile the BOM row against it. Hip_roll margin is now **2.83× @1.485 kg** (PASS).
- **Split decisions** — trunk shell (and any part >220 mm) splits pending the
  user's confirmed printer bed size.
- **Bench check before full build** — mixed C018+SC-0043 FT-SCS enumeration at
  500 kbps on the URT-1; if the one-bus power-tap layout misbehaves, fall back
  to two buses (BOM §7).

---

## 8. REV-A → REV-B before/after stability table

| Metric | REV-A (pre) | REV-B (post) |
|---|---|---|
| Overall height | 412 mm | **394 mm** |
| Sole width (Y) | 20 mm | **44 mm** |
| Sole length (X) | 30 mm | **40 mm** |
| Neck pitch axis z | 203 mm | **185 mm** |
| Carrier board-top z | 101 mm | **72 mm** |
| Whole-robot CoM height above floor | not computed | **162.5 mm** (target ≤180, PASS) |
| Lateral tipping angle | — | **16.8°** (half-base 49 mm) |
| Forward tipping angle | — | **7.0°** (half-base 20 mm; **binding direction**) |
| hip_roll verdict | PASS 3.65× @1.15 kg (estimate) | **PASS 2.83× @1.485 kg real** (2.72 N·m / 0.961 N·m) |

Sources: NVIDIA carrier spec SP-11324; Feetech ST-3215-C018 datasheet;
`dims/dimensions.md`; `ASSEMBLY_REPORT.md` §5 (CoM/statics) and §6 (torque).
Mass = 1.38 kg frame+hardware (real PETG volume ×1.27 + datasheet hardware),
1.485 kg with the +105 g fastener/horn/bearing/wiring lump at the assembly CoM.
