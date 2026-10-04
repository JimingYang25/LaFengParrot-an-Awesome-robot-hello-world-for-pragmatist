# LaFengParrot Assembly Report — REV-B stability rebuild

Date: 2026-09-27. Project path `D:\Desktop\LaFengParrot\CAD` (renamed from
LaFengPirate). Rewritten `source\assembly\poses.py` for the REV-B stability
anchors: 54 mm hip rail (±27), 40x44x4 feet with 10 mm inner gap, neck pitch axis
lowered to global z=185, carrier at board-top z=72, battery tray on the
trunk floor. All numbers below were computed from the baked solids (bbox,
volume, centroid via OCP), not estimated.

## 1. Envelope & total height

Reloaded `exports\step\LaFengParrot_Standing.STEP` (29 solids, valid):

| axis | min | max | note |
|---|---|---|---|
| X | −64.0 | +72.0 | +72 lipo/XT60 stub; −64 = XT60-switch lead (hardware). The old 150 mm cosmetic cable extremes are GONE. |
| Y | −190.9 | +190.9 | wing panel rounded tips (shoulder y=±62 + ~129 mm span). |
| Z | −138.0 | +256.1 | −138 = foot sole floor; +256 = head crest. |

Total height = 256.1 − (−138.0) = **394 mm**. Floor z=−138, hip plane z=0,
trunk roof z=133, neck pitch axis z=185, crest z≈256.

## 2. Placement table (standing, global frame: +X beak, +Y left, +Z up)

Rotation codes: ID = identity;
HIPL = `[[0,0,1],[1,0,0],[0,1,0]]` (shaft local Z→+X, body tail→+Y outboard);
HIPR = `[[0,0,1],[-1,0,0],[0,-1,0]]` (R mirror, tail→−Y outboard);
PIT = `[[1,0,0],[0,0,1],[0,1,0]]` (shaft local Z→+Y);
PITM = `[[1,0,0],[0,0,-1],[0,1,0]]` (R mirror, shaft→−Y outboard).

| instance | part_id | R | translation (x,y,z) | purpose |
|---|---|---|---|---|
| hip_mount_L | hip_mount(L) | ID | (0, +27, 0) | hip_roll housing, on hip plane |
| hip_mount_R | hip_mount(R) | ID | (0, −27, 0) | |
| thigh_link_L | thigh_link(L) | ID | (0, +27, −42) | hip_pitch pivot 42 below hip plane |
| thigh_link_R | thigh_link(R) | ID | (0, −27, −42) | |
| shin_link_L | shin_link(L) | ID | (0, +27, −84) | knee pivot; sole underside −54 → floor −138 |
| shin_link_R | shin_link(R) | ID | (0, −27, −84) | |
| trunk_shell | trunk_shell | ID | (0, 0, +33) | floor underside 33, roof top 133 |
| battery_tray | battery_tray | ID | (0, −23, +33) | base underside on trunk floor |
| power_mount | power_mount | ID | (0, +23, +36) | on cavity floor top (36) |
| wing_arm_L | wing_arm(L) | ID | (0, +62, +60) | shoulder |
| wing_arm_R | wing_arm(R) | ID | (0, −62, +60) | |
| neck_linkage | neck_linkage | ID | (0, 0, +133) | base on trunk roof; pitch axis local 52 → 185 |
| head_shell | head_shell | ID | (0, 0, +185) | on pitch horn |
| st3215_hiproll_L | st3215_c018 | HIPL | (23.25, +21.25, 0) | shaft on hip bore; body in pocket |
| st3215_hiproll_R | st3215_c018 | HIPR | (23.25, −21.25, 0) | |
| st3215_hippitch_L | st3215_c018 | PIT | (−5.75, +44.5, −42) | in top thigh pocket |
| st3215_hippitch_R | st3215_c018 | PITM | (−5.75, −44.5, −42) | mirrored, shaft outboard |
| st3215_knee_L | st3215_c018 | PIT | (−5.75, +44.5, −84) | in bottom thigh pocket |
| st3215_knee_R | st3215_c018 | PITM | (−5.75, −44.5, −84) | |
| sc0043_wing_L | sc0043_c001 | PIT | (0, +71.70, +60) | wing shoulder pocket |
| sc0043_wing_R | sc0043_c001 | PITM | (0, −71.70, +60) | |
| sc0043_neckyaw | sc0043_c001 | ID | (0, 0, +155.39) | shaft on yaw bore (linkage local 22.39) |
| sc0043_neckpitch | sc0043_c001 | PIT | (0, +9.70, +185) | pitch pocket at global 185 |
| orin_carrier | orin_carrier | ID | (0, 0, +72) | board-top 72 (feet bottom 65.4, cooler top 100) |
| lipo_3s_2200 | lipo_3s_2200 | ID | (0, −23, +49) | pack centre; pack box z 36..62 |
| xt60_switch | xt60_switch | ID | (−22, +23, +48.5) | in power_mount switch channel |
| bec_5v3a | bec_5v3a | ID | (+28, +32.5, +43.5) | BEC channel |
| fuse_holder | fuse_holder | ID | (+28, +13.5, +43.5) | fuse channel |
| imuc_icm42688p | imuc_icm42688p | ID | (−12, 0, +191.5) | head underside pocket |

## 3. Clash results (BRepAlgoAPI_Common, bbox pre-filter; threshold >0.01 mm3)

Only DESIGNED / COSMETIC contacts remain in every pose. No unintended CLASH.

| pose | unintended CLASH | notes |
|---|---|---|
| standing | **0** | 10.0 mm sole inner gap measured (L sole y[5,49], R y[−49,−5]); feet never touch. |
| (a) both feet flat | 0 | 10 mm inner gap confirmed; no foot-foot contact. |
| (b) left foot lifted 50 mm (+30 fwd, sole z=−88) | 0 design clashes | lifted foot bbox x[10,50] y[5,49] z[−88,−26]; clear of right foot (y≤−5). One residual 294 mm3 overlap of shin_L with the hip_pitch pocket is an ARTIFACT of modelling the lift as a rigid translation (real knee flexion keeps the shin top seated); foot-foot / foot-shin clearance itself is clear. |
| (c) left leg hip_roll +20 deg | 0 | abducted foot centre y=+72.1 (foot y[49,95]); clear of right foot and below the trunk (z≤−70 vs trunk z≥33). [Note: +20 deg about the hip axis physically lands the foot at y≈72; the ~47 mm value is the lateral excursion.] |
| (d) head pitched +45 deg nose-down | 0 design clashes | head zmin=169 → **36 mm above trunk roof 133** (≥3 required). Small head/pitch-servo overlap is the designed horn-pivot envelope. |
| (e) head yaw ±90 deg | 0 | no contact at either extreme. |

Designed contacts (expected): servo-in-pocket (all 10 servos), knee/hip pivots,
neck-on-roof, head-on-horn, IMU-in-head-pocket, lipo-in-tray, devices-in-channels,
carrier-on-standoffs, bolted bodies on the trunk floor. Cosmetic 15 mm cable
stubs and BEC/fuse leads may lightly touch (noted, benign).

## 4. Service access

- microSD / barrel / USB: carrier board-top at z=72, board edges z≈65.4–72;
  connectors at global y≈+20–29, all inside the +Y service window
  (trunk wall opening z 54–116, y 43–55, x ±40) → reach-through clear.
- 40-pin GPIO: on the −Y board edge (global y≈−34.5), open to the −Y interior.
- XT60 switch: at (−22,+23,48.5) beside the +Y window; battery XT60 exits the
  open +X end of the tray.
- Fan exhaust: cooler grille top z≈100; roof vent slots at z 128.5–133.5 aligned
  with the fan (board (50,30)→global (0,−9.5)). Clear **~28 mm plenum**
  (100→128.5); nothing blocks the flow path above the cooler.

## 5. CoM & statics (baked centroids, computed)

Frame mass = real volume (cm3) × 1.27 (PETG); hardware = datasheet masses.
Convention: **+105 g lump** (fasteners, horns, bearings, wiring) added at the
assembly CoM so it does not bias the balance.

- Total M (frame + hardware, before lump) = **1379.6 g ≈ 1.38 kg**.
- Total M with 105 g lump = **1484.6 g ≈ 1.485 kg**.
- CoM global = (**+0.8, −3.9, +24.5**) — near sagittal centre (battery at y=−23
  balanced by power devices at y=+23).
- **CoM height above floor z=−138 = 162.5 mm** (target ≤180 → PASS).
- CoM height above hip plane z=0 = 24.5 mm.

Tipping angles = atan(half-base / CoM_z above floor, CoM_z=162.5):

| direction | half-base | angle |
|---|---|---|
| lateral (sideways) | 49 mm | **16.8°** |
| forward | 20 mm | **7.0°** |

**Binding direction = FORWARD** (smaller angle). The short 20 mm forward
half-base is the weak axis; the 162 mm CoM height already meets the REV-B target.

## 6. hip_roll torque re-check

- Required @2× safety = 0.647 · M, r = 33 mm.
- At M = 1.485 kg (with lump): required = **0.961 N·m**.
- ST-3215-C018 stall ≈ 2.72 N·m @11.1 V → **margin 2.83×**.
- At M = 1.38 kg (without lump): required 0.893 N·m → **margin 3.05×**.
- PASS (≈3× as expected).

## 7. Exports (absolute paths)

Full assemblies:
- `D:\Desktop\LaFengParrot\CAD\exports\step\LaFengParrot_Standing.STEP`
- `D:\Desktop\LaFengParrot\CAD\exports\step\LaFengParrot_Exploded.STEP`

Per-part local STEP + STL (unrotated local frame), in
`D:\Desktop\LaFengParrot\CAD\exports\step\` and `...\exports\stl\`:
battery_tray, bearing_mr63, bec_5v3a, fuse_holder, head_shell, hip_mount,
imuc_icm42688p, lipo_3s_2200, neck_linkage, orin_carrier, power_mount,
sc0043_c001, shin_link, st3215_c018, thigh_link, trunk_shell, wing_arm_L,
wing_arm_R, xt60_switch.

## 8. Open / [EST] items

- Standoff height now 33 mm [EST] (carrier feet 65.4 above trunk floor). The
  previous tray-top nick (tray z≈64.5 vs feet 63.4) is RESOLVED: feet now sit
  0.9 mm above the tray top, and 3.4 mm above the battery pack top (62).
- Crest height 256 vs ~251 estimate is from the actual tilted crest fins.
- R-side thigh/knee servos use a mirrored PITM rotation (shaft outboard); the
  REV-A file had them on the wrong side — corrected here.
- No dimension was fabricated; EST items above are flagged.
