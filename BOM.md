# LaFengParrot — BOM & Engineering Baseline (Sep 2026, All-Domestic Edition)

**Project:** Parrot-shaped pet robot, ~25 cm class, analog of pollen-robotics/microduck.
**Compute (OWNED ✅, purchased 2026-09):** NVIDIA Jetson Orin Nano Super 8 GB **official developer kit** — module TW-T013-8GB mounted on the NVIDIA **reference carrier** with the **stock active cooler (heatsink+fan) pre-mounted**; JD [item 10149183026930](https://ic-item.jd.com/10149183026930.html). **The robot carries the reference carrier + stock cooler exactly as they ship** (cost ¥0, but their mass counts in §2); the A603 carrier / Waveshare cooler / NVMe are **NOT purchased**. Module: 69.6×45 mm, 260-pin SO-DIMM, 7/15/25 W, 67 INT8 TOPS.
**Behaviors (user-frozen v1):** bipedal WALK (microduck RL method), wing FLUTTER ×2, neck SHAKE/tilt. **NO flight.**
**Pricing snapshot:** 2026-09-27 (Sep 2026), CNY. **ALL materials purchasable inside mainland China** (Taobao/Tmall/JD/1688/domestic official flagship stores), domestic shipping only — no foreign-shipping options anywhere. Every value marked [ESTIMATE] is an inference, not a confirmed price; nothing was fabricated. FX ≈ 7.2 CNY/USD [ESTIMATE].

---

## 0. Scope — CORE vs OPTIONAL / DEFERRED

**CORE (v1, this BOM, 10 DOF, one servo bus):**
| Group | DOF | Servo |
|---|---|---|
| Legs ×2 — hip_roll + hip_pitch + knee_pitch (3 DOF/leg, BDX/OpenDuck-style) | 6 | Dynamixel XC330-M288-T |
| Wings ×2 — single flap DOF each (doubles as balance appendages during gait) | 2 | Dynamixel XL330-M288-T |
| Neck — yaw + pitch | 2 | Dynamixel XL330-M288-T |
| **Total core** | **10** | **6× XC330 + 4× XL330** |

**OPTIONAL (labeled, NOT core — v2+):**
- Legs → mirror microduck's *actual* 5 DOF/leg (add hip_yaw ±27°, ankle ±90°): **+4 servos ≈ +¥3,200, +46 g**. Microduck's real legs are 5 DOF (`hip_yaw, hip_roll, hip_pitch, knee, ankle` — 10 of its 15 servos); the extra yaw/ankle refine the waddle but the RL method (PPO in MuJoCo Warp, 50 Hz ONNX) transfers either way. [RL-README]
- Head/crest roll (+1), beak articulation, tail, camera, speaker/TTS, ToF, gamepad (teleop).

**DEFERRED (out of core, per scope):** everything above not in CORE or OPTIONAL.

---

## 1. Research corrections vs the working assumptions (read first)

1. **Microduck legs are 5 DOF, not 3** — `hip_yaw / hip_roll / hip_pitch / knee / ankle` per side, 10 servos; plus 4 head/neck servos + 1 beak servo = 15. There are **no wing or tail servos in microduck**. The beak is deliberately excluded from the RL action vector and daemon-driven. Its real geometry (from the shipping MuJoCo MJCF): trunk at z=0.12 m standing, hip half-spacing ≈34 mm, thigh ≈42 mm, shin ≈50 mm, crouch pose = hip_pitch 26° / ankle 26° / knee ~0°, robot 250×140 mm, **780 g**. [MJCF][CONST][ROBOTD-DESIGN]
2. **XL330/XC330-M288-T share a hard 6.0 V absolute max** — there is no 7.4 V operation for these SKUs (the 9–12 V row in the eManual belongs to the XC330-T288, a different model). A 2S pack (8.4 V charged) overvolts them. Microduck *does* run XL330s straight off the 2S NP-F550 rail (6.5–8.2 V) and clears the overvoltage-shutdown bit (shutdown=52) — a proven-but-out-of-spec hack. **This build does not copy that**: servos run from a regulated 6.0 V rail. [ROBOTD-DESIGN][XL330][XC330]
3. **Dynamixel bus connector is 3-pin JST-EH** (Robot Cable-X3P), not 4-pin. X4P is RS-485 Dynamixels only. [XL330][CN-CHANNEL]
4. **No surveyed Orin carrier accepts 2S (7.4 V) directly** — every board's input regulator cuts out at 9 V minimum. The LiPo that fits all 9–20 V carriers is **3S 11.1 V (9.9–12.6 V)**. [CARRIER]
5. **The open sibling Open Duck Mini independently converged on XC330 legs** — repo README: *"I switched to using `xc330-M288-T` servomotors instead of `xl330-M288-T` for the legs. They are more expensive, but way more powerful."* This is external validation of the torque analysis in §3. [ODM]
6. **Domestic-channel price correction (Sep 2026):** the earlier "MicroDuck crunch ¥950–1800" figure was overstated. Verified domestic prices today: **XL330-M288-T ¥95 (智能佳机器人, authorized distributor, in stock, verified 2026-09-02) / ¥238 (WowRobo, 48 h ship, 100+ orders) / ¥120–188 (1688)**; **XC330-M288-T ≈ ¥800 (multiple Taobao "韩国原装正品" listings), ¥700–900 band**. ROBOTIS has no Tmall/JD flagship — its China office (china@robotis.com) directs buyers to Taobao, where its **first authorized partner since 2007, 智能佳机器人 (BJRobot, bjrobot.jd.com / rosrobot.cn)**, sells genuine units. The 20 g + ≥0.9 N·m + Dynamixel-bus niche has **no domestic equivalent** as of Sep 2026 (Feetech STS3215 = 3× heavier + incompatible protocol; Unitree S288 = private 1-Wire protocol; Feetech SC09 = 0.23 N·m, insufficient) — so the proven servo selection stands and is buyable domestically. [CN-CHANNEL][CN-BACKUP]

---

## 2. Mass build-up (bottom-up)

Target: **≤ 1.15 kg** (microduck is 780 g; Orin compute stack replaces RK3566/Radxa Zero 3W). Worst-case design point for the torque budget: **1.20 kg**.

| # | Item | Qty | Unit mass (g) | Subtotal (g) | Status |
|---|---|---|---|---|---|
| 1 | Jetson Orin Nano Super module (bare) | 1 | 15 | 15 | [ESTIMATE 13–30 g, not published; SO-DIMM-class] |
| 2 | Reference carrier + stock active cooler + feet (dev-kit board assembly, owned) | 1 | 160 | 160 | [derived: verified dev-kit board assembly 0.175 kg (NVIDIA Carrier Spec SP-11324-001, "The Developer Kit Weighs 0.175kg") − module 15 g = 160 g; ESTIMATE split: carrier ~100 g / cooler ~50–55 g / feet ~10–15 g] |
| 3 | XC330-M288-T (legs) | 6 | 23 | 138 | datasheet |
| 4 | XL330-M288-T (wings + neck) | 4 | 18 | 72 | datasheet |
| 5 | JST-EH 3-pin bus cables | 12 | 2 | 24 | [ESTIMATE per cable] |
| 6 | Hobbywing UBEC 10 A (6 V rail) | 1 | 45 | 45 | [ESTIMATE] |
| 7 | 3S 11.1 V 2200 mAh LiPo (XT60) | 1 | 185 | 185 | listing |
| 8 | Fuse holder + 10 A fuse + XT60 switch | 1 set | 30 | 30 | [ESTIMATE] |
| 9 | PETG frame: trunk shell + leg links + head shell | — | 230 | 230 | [ESTIMATE; filament ~0.6 kg incl. ~15% supports/iterations → ~0.5 kg parts, split across legs/trunk/head; duck trunk core 264 g incl. electronics; trunk sized for the dev-kit stack — see CAD note] |
| 10 | Fasteners, servo idler horns, bearings (MR63/MR84) | — | 60 | 60 | [ESTIMATE] |
| 11 | ICM-42688-P body IMU breakout | 1 | 4 | 4 | [ESTIMATE] |
| 12 | Wiring, sleeving, bulk capacitor (2200 µF) | — | 45 | 45 | [ESTIMATE] |
| | **TOTAL (robot-mounted)** | | | **≈ 1008 g ≈ 1.01 kg** | |

Notes: 2 spare servos (1× XC330, 1× XL330) are purchased but not mounted. The balance charger (格氏 B3) and the USB→TTL bench adapter are bench equipment, not robot-mounted. If a second battery is carried for hot-swap, +185 g (→ 1.19 kg, still inside the 1.20 kg design point). The robot flies the **dev-kit board assembly as-is**: its verified 175 g (carrier + module + stock cooler + feet) is only ~4 g lighter than the A603 + Waveshare + NVMe stack it replaces (179 g), so total mass stays ≈ 1.01 kg.

**CAD / packaging note:** the trunk must fit the full dev-kit envelope **103 × 90.5 × 34.8 mm** (height explicitly includes feet, carrier board, module and thermal solution — verified [DEVKIT]). Plan trunk interior ≥ **105 × 92 mm footprint × ≥ 36 mm tall**, top **vented** so the stock cooler's fan (blows upward off the heatsink) gets airflow; mount on standoffs matching the carrier's ~5 mm feet so the bottom connectors (USB-A, DP, DC jack) clear the deck. This is the real tradeoff vs the A603 (87×52×26 mm): roughly 2× the footprint and 1.4× the height, so the printed trunk is a bit larger (+~10–20 g frame [ESTIMATE], at the margin of the 230 g line) — zero extra cost, already in hand.

**Variant — all-Feetech servo build (§7):** servo mass 356 g (+146 g vs the 210 g Dynamixel mix) → robot ≈ 1.15 kg (at the target ceiling; no second battery). Binding hip_roll @2× = 0.91 N·m vs ST-3215-C018 ≈ 2.72 N·m @11.1 V → **PASS 3.0×** (full details in §7).

---

## 3. Joint-torque budget

**Model (worst-case statics + dynamic margin):**
- Robot mass **M = 1.20 kg** (worst-case design; build estimate 1.01 kg) → weight **W = M·g = 11.77 N** (g = 9.81).
- **Single-leg support** worst case (the other leg mid-swing), body on one leg, crouched gait (hip_pitch 26° / knee ~0° mirroring microduck's HOME pose).
- Lever arms **r** (mirrored from microduck's published MJCF, scaled): hip_roll r = 40 mm (hip half-spacing 34 mm + body-roll margin), hip_pitch r = 25 mm (CoM sagittal offset during stride), knee_pitch r = 25 mm, optional ankle r = 15 mm.
- **Dynamic safety margin 2.0×** on the static value (covers weight transfer, lateral accel, ground reaction spikes; the RL gait is 50 Hz, not ballistic).
- Servo stall values (datasheet): XL330-M288-T **0.52 N·m @5 V / 0.60 N·m @6 V**; XC330-M288-T **0.93 N·m @5 V / 1.10 N·m @6 V**. Stall = transient peak; keep sustained load ≤ ~50% stall (the 2× margin does that).

| Joint | r (mm) | Static τ = W·r (N·m) | Required τ ×2 (N·m) | XL330 @6 V (0.60) | XC330 @5 V (0.93) | XC330 @6 V (1.10) | **Verdict** |
|---|---|---|---|---|---|---|---|
| hip_roll | 40 | 0.47 | **0.94** | FAIL (0.64×) | MARGINAL (0.99×) | **PASS (1.17×)** | ✅ XC330 @6 V |
| hip_pitch | 25 | 0.29 | **0.59** | MARGINAL (1.02×) | PASS | PASS | ✅ XC330 |
| knee_pitch | 25 | 0.29 | **0.59** | MARGINAL (1.02×) | PASS | PASS | ✅ XC330 |
| wing (flap) | 90 arm | ~0.02 | <0.15 | PASS | — | — | ✅ XL330 |
| neck (yaw/pitch, 140 g head @55 mm) | 55 | 0.08 | 0.15 | PASS | — | — | ✅ XL330 |

**Pass/fail conclusion:**
- **XL330 legs FAIL** for this robot: the binding joint (hip_roll, frontal-plane weight transfer) needs 0.94 N·m at the 1.2 kg design point vs 0.60 N·m available — a 1.6× shortfall. The duck itself only survives because it weighs 0.78 kg (hip_roll req 0.61 ≈ 0.60, effectively zero margin) **and** overvolts to 6.5–8.2 V.
- **XC330-M288-T legs PASS** with the 2× margin when run at **6.0 V** (1.10 N·m vs 0.94 required = 1.17× on the 2×-scaled load ≈ 2.3× vs the static base). At 5 V the same joints are marginal at 1.2 kg (0.93 vs 0.94), so **run the servo rail at 6.0 V**. At the **1.01 kg build** hip_roll needs only 0.79 N·m → PASS with **1.39×**; the PASS ceiling is **M = 1.40 kg** (1.10 / 0.785), so legs stay PASS for any build up to that mass.
- Wings and neck are light-load joints → **XL330** is correct there.

**Mass sensitivity — the binding hip_roll joint (required @2× = 0.785·M):**
| Robot mass | Required | XL330 @6 V | XC330 @5 V | XC330 @6 V |
|---|---|---|---|---|
| 0.78 kg (microduck) | 0.61 | FAIL (−2%, duck only works overvolted) | PASS | PASS |
| 1.01 kg (this build, dev-kit stack) | 0.79 | FAIL | PASS | PASS (1.39×) |
| 1.20 kg (worst, incl. hot-swap battery) | 0.94 | FAIL | MARGINAL | **PASS (1.17×)** |
| 1.40 kg (PASS ceiling) | 1.10 | FAIL | FAIL | MARGINAL (= stall, 0 margin) |

**Feetech-variant check (§7):** at M = 1.15 kg, hip_roll required @2× = 0.91 N·m; **ST-3215-C018 @11.1 V ≈ 2.72 N·m → PASS (3.0×)**; hip_pitch/knee 0.59 N·m → PASS; wings 0.15 N·m vs SC-0043 0.216 N·m → PASS (1.4×).

**Servo decision (single bus, single family):** legs **6× XC330-M288-T**, wings/neck **4× XL330-M288-T** → 210 g total servo mass, one Protocol-2.0 TTL daisy-chain, one 6 V rail (mixing is drop-in: same protocol, same 3-pin connector, same baud table — verified). [XC330][XL330]
**Domestic availability of this exact selection: CONFIRMED** — 智能佳机器人 (authorized) + Taobao resellers stock both SKUs today (see §Domestic sourcing guide); torque conclusion stands unchanged. [CN-CHANNEL]

---

## 4. Bus & control architecture (mirrors microduck's proven setup)

- One **half-duplex TTL bus @1 Mbps**, Dynamixel Protocol 2.0, all 10 servos daisy-chained (IDs unique), exactly like microduck's `/dev/ttyS2` @1 Mbaud (which carries 15 servos + the IMU board on one bus). Control loop: one `sync_read` (pos/vel/current) + one `sync_write` @50 Hz, matching microduck's loop. [ROBOTD-DESIGN]
- **On-robot interface:** reference-carrier 40-pin header **UART1** (pin 8 TX / pin 10 RX, 3.3 V) + **SN74LVC1G126** (single tri-state buffer, SOT-23-5, active-high enable) wired to the single DATA line; a free GPIO drives the buffer enable: HIGH = transmit (Orin drives the bus), LOW = receive (buffer hi-Z, servo drives). No level shifter needed (bus is 3.3 V, 5 V-tolerant). Orin UART synthesizes up to ~4.25 Mbps; 1 Mbps is the proven sweet spot for 10 joints. [XC330][CARRIER]
  - SN74LVC1G126 / SN74LVC126A / 74HC125 are stocked domestically on **LCSC 立创商城 (¥0.5–2/pc)** and Taobao. [CN-BACKUP]
- **Bench interface (domestic, replaces imported U2D2):** **Feetech URT-1** USB→485→TTL half-duplex adapter (Taobao 飞特官方, **¥30–60 [EST]**, auto direction-control — no GPIO toggling, supports 1 Mbps). It is electrically a generic half-duplex TTL transceiver; the Dynamixel protocol lives in the software driver, so it bridges an XL330/XC330 bus fine (verify direction wiring on the bench). Backup options: FASHION STAR UC-01 (¥20–40 [EST], auto-direction), or the genuine **ROBOTIS U2D2 sold domestically by 智能佳** (JD item 10152431689448, ¥250–350 [EST]) if you want Dynamixel Wizard 2.0 tooling. [CN-CHANNEL][CN-BACKUP]
- **Not used in the primary build:** Feetech STS3215 — different packet protocol (0xFF 0xFF / 8-bit checksum vs Dynamixel Protocol 2.0 / 16-bit CRC) and 3× heavier; it **cannot share the Dynamixel daisy-chain** (it needs its own UART + transceiver + Feetech SDK). If the all-Feetech architecture is adopted (§7), the Feetech bus becomes the single bus for all 10 servos. [STS][FTECH-BUILD]

---

## 5. Power architecture (voltages AND currents consistent)

Battery: **3S 11.1 V 2200 mAh LiPo, XT60** (9.9–12.6 V) — the only LiPo that fits every surveyed carrier's 9–20 V input; 2S (max 8.4 V) cannot boot any of them. [CARRIER][PERIPH]

```
3S 11.1 V 2200 mAh (XT60)
 ├─ 10 A inline fuse → XT60 switch
 │   ├─ reference carrier barrel (9–20 V):  Orin rail
 │   │    15 W walking mode ≈ 1.4 A avg @11.1 V (≤3 A board rating OK);
 │   │    25 W boost ≈ 2.3 A — bench only; set battery cutoff ≥ 9.6 V
 │   └─ Hobbywing UBEC 10 A → 6.0 V servo rail (setpoint 5.9–6.0 V, abs max 6.0 V)
 │        XL330/XC330-M288-T all ≤6.0 V cap — NEVER feed LiPo directly
 │        Realistic gait draw ≈ 3–6 A bursts; theoretical all-stall = 19.9 A
 │        (6×2.15 + 4×1.74) → UBEC 10 A cont / 15 A peak + 2200 µF low-ESR
 │        bulk cap at the first servo node; 15 A slow-blow fuse optional on rail
 └─ (optional) balance plug JST-XH → 格氏 B3 balance charger (CORE purchase, §6)
```

Bench: servo rail from **Mean Well LRS-50-5 (5 V/10 A)** — domestic via Taobao/1688 [EST ¥71–99]; carrier from its own 19 V PSU or the 3S pack. [SERVO][PERIPH]

Runtime: 3S 2200 mAh = 24.4 Wh; ~15–19 W average draw (Orin + 10 servos) → **~1.2–1.5 h** [ESTIMATE], vs microduck's ~1 h on NP-F550 (2S 2600 mAh ≈ 19 Wh, implied 19 W).

---

## 6. Recommended purchase list — ALL-DOMESTIC (CNY, Sep 2026)

All lines ship from inside mainland China. Prices: verified listing or [ESTIMATE] band as marked. Domestic-specific keywords and channels in the §"Domestic sourcing guide".

| # | Part | Qty | Unit ¥ | ¥ | Mass mounted (g) | Store link | Channel / note |
|---|---|---|---|---|---|---|---|---|
| 1 | NVIDIA reference carrier + stock active cooler + feet (dev-kit board assembly, owned) — replaces A603 | 1 | 0 (included) | 0 | 160 | [JD商品页·已购开发套件](https://ic-item.jd.com/10149183026930.html) | NOT PURCHASED — 随开发者套件附带; 103×90.5×34.8 mm; mass per §2 (verified 175 g assembly) |
| 2 | Waveshare Orin-FAN-PWM cooler — NOT purchased (stock NVIDIA cooler used, pre-mounted) | 0 | — | 0 | 0 | [微雪·官方商品页](https://www.waveshare.com/orin-fan-pwm.htm) | 链接仅作参考; 质量含于 §2 第 2 行 |
| 3 | WD SN740 2242 NVMe — DEFERRED (dev kit boots from microSD; ONNX policy is tiny; NVMe only speeds host data/training, not robot inference) | 0 | — | 0 | 0 | [JD搜索 SN740 2242](https://search.jd.com/Search?keyword=SN740%202242&enc=utf-8) | deferred, not core |
| 4 | Dynamixel XC330-M288-T (legs) | 6 | 800 | 4,800 | 138 | [淘宝搜索 XC330-M288-T 舵机](https://s.taobao.com/search?q=XC330-M288-T%20%E8%88%B5%E6%9C%BA) | 智能佳 / Taobao "韩国原装正品" [EST 700–900]; 确认 **-T (TTL)** 后缀 |
| 5 | Dynamixel XL330-M288-T (wings/neck) | 4 | 238 | 952 | 72 | [智能佳·淘宝商品页 ¥95](https://item.taobao.com/item.htm?id=638117456346) · [WowRobo·淘宝商品页 ¥238](https://item.taobao.com/item.htm?id=929725677792) | band ¥95–238; 智能佳库存间歇, WowRobo 48h发货 |
| 6 | Spares: XC330 ×1 + XL330 ×1 | 2 | — | 1,038 | 0 (spares) | [淘宝搜索 XC330](https://s.taobao.com/search?q=XC330-M288-T%20%E8%88%B5%E6%9C%BA) · [智能佳·XL330 商品页](https://item.taobao.com/item.htm?id=638117456346) | 同 4/5 渠道 |
| 7 | JST-EH 3-pin bus cables (Robot Cable-3P compatible), ~20 pc | 20 | 3 | 60 | 24 | [淘宝搜索 JST-EH 3P 舵机线](https://s.taobao.com/search?q=JST-EH%203P%20%E8%88%B5%E6%9C%BA%E7%BA%BF) | 智能佳 "Robot Cable-3P" 或通用 JST-EH 3P [EST 2–5/pc]; 确认3pin非4pin |
| 8 | SN74LVC1G126 ×5 (bus transceiver + spares) | 5 | 1 | 5 | ~0 | [立创商城搜索 SN74LVC1G126](https://www.szlcsc.com/search?q=SN74LVC1G126) | LCSC/淘宝 [¥0.5–2/pc] |
| 9 | Feetech URT-1 USB→TTL half-duplex adapter (bench) | 1 | 45 | 45 | 0 (bench) | [淘宝搜索 飞特 URT-1 调试板](https://s.taobao.com/search?q=%E9%A3%9E%E7%89%B9%20URT-1%20%E8%B0%83%E8%AF%95%E6%9D%BF) | 淘宝 飞特官方 [EST 30–60]; U2D2 国内备选见§4 |
| 10 | Hobbywing UBEC 10 A (6 V servo rail) | 1 | 80 | 80 | 45 | [淘宝搜索 好盈 UBEC 10A](https://s.taobao.com/search?q=%E5%A5%BD%E7%9B%88%20UBEC%2010A) | 好盈官方店/淘宝 [EST 40–80] |
| 11 | 3S 11.1 V 2200 mAh LiPo XT60 (+1 spare) | 2 | 80 | 160 | 185 | [淘宝搜索 3S 2200mAh 航模锂电池 XT60](https://s.taobao.com/search?q=3S%202200mAh%20%E8%88%AA%E6%A8%A1%E9%94%82%E7%94%B5%E6%B1%A0%20XT60) | 淘宝/1688 [EST 60–120] |
| 12 | **格氏 Gens Ace B3 balance charger (CORE)** | 1 | 105 | 105 | 0 (bench) | [淘宝搜索 格氏 B3 平衡充](https://s.taobao.com/search?q=%E6%A0%BC%E6%B0%8F%20B3%20%E5%B9%B3%E8%A1%A1%E5%85%85) | 格氏官方店/淘宝 [EST 80–130] |
| 13 | XT60 power switch + inline 10 A fuse + holder | 1 set | 20 | 20 | 30 | [淘宝搜索 XT60 开关 航模 保险丝座](https://s.taobao.com/search?q=XT60%20%E5%BC%80%E5%85%B3%20%E8%88%AA%E6%A8%A1%20%E4%BF%9D%E9%99%A9%E4%B8%9D%E5%BA%A7) | 淘宝 [EST 10–25] |
| 14 | ICM-42688-P 6-axis SPI breakout (body IMU) | 1 | 60 | 60 | 4 | [淘宝搜索 ICM42688P 六轴IMU](https://s.taobao.com/search?q=ICM42688P%20%E5%85%AD%E8%BD%B4IMU) | 淘宝 GY模块 [EST 25–60] |
| 15 | MPU6050 breakout (optional head IMU) | 1 | 10 | 10 | 2 | [淘宝搜索 MPU6050 模块 GY-521](https://s.taobao.com/search?q=MPU6050%20%E6%A8%A1%E5%9D%97%20GY-521) | 淘宝 |
| 16 | PETG filament 1 kg (PolyMaker PolyLite / 金质) | 1 | 70 | 70 | 230 (printed) | [淘宝搜索 PolyLite PETG 1kg](https://s.taobao.com/search?q=PolyLite%20PETG%201kg) | PolyMaker官方店/淘宝 [EST 60–90] |
| 17 | M2/M2.5/M3 304 screw kit | 1 | 20 | 20 | — | [淘宝搜索 M2 M2.5 M3 螺丝套装 304](https://s.taobao.com/search?q=M2%20M2.5%20M3%20%E8%9E%BA%E4%B8%9D%E5%A5%97%E8%A3%85%20304) | 淘宝 [EST 15–35] |
| 18 | MR63/MR84 bearings (~25 pc) | 25 | 1 | 25 | — | [淘宝搜索 MR63ZZ MR84ZZ 微型轴承](https://s.taobao.com/search?q=MR63ZZ%20MR84ZZ%20%E5%BE%AE%E5%9E%8B%E8%BD%B4%E6%89%BF) | 淘宝 [EST 1–5/pc] |
| 19 | FPX330-H101 idler horn set (4 pc) — **1 set as reference; primary path = PETG 3D print** | 1 | 65 | 65 | — | [淘宝搜索 FPX330-H101 支架套装](https://s.taobao.com/search?q=FPX330-H101%20%E6%94%AF%E6%9E%B6%E5%A5%97%E8%A3%85) | 淘宝 [EST 50–80/set]; printed horns ~¥1 filament |
| 20 | PET braided sleeving 2 m | 2 | 2.5 | 5 | — | [1688搜索 编织网管 包线管](https://s.1688.com/selloffer/offer_search.htm?keywords=%E7%BC%96%E7%BB%87%E7%BD%91%E7%AE%A1%20%E5%8C%85%E7%BA%BF%E7%AE%A1) | 1688/淘宝 |
| | **TOTAL (all-domestic)** | | | **≈ ¥7,523** | **≈ 1,008 g (per §2)** | — | |

**Link legend:** `官方商品页` = verified manufacturer/official product page (live-checked); `商品页·店名` = verified distributor item page (Taobao/JD item IDs from 2026-09-02 verified research — these block automated crawlers but open normally in a browser); `淘宝搜索/JD搜索/1688搜索/立创商城搜索` = pre-filled search URL for the exact Chinese keyword (also bot-walled, opens in browser).

Mounted robot mass ≈ 1.01 kg (§2) ✓ within target; servo cost = **¥6,790 ≈ 90% of the total** — the biggest cost driver. (Prior editions: ≈ ¥10,330 → all-domestic ≈ ¥9,290 → **≈ ¥7,523** after removing A603 ¥1,400, Waveshare cooler ¥67 and NVMe ¥300 — the compute stack is the owned dev-kit reference carrier + stock cooler at ¥0.)

---

## 7. Cheaper servo architecture (Dynamixel stays the premium option — fully costed labeled alternative)

1. **Enterprise/tiered pricing via the authorized distributor:** contact **智能佳机器人** (china@robotis.com / 400-099-1872 / rosrobot.cn) as a research buyer — they offer 企业会员 bulk invoicing and tiered pricing at 5-/10-unit quantities; the ¥95 XL330 price is their listed SKU (intermittent stock). For 12 servos this is the biggest legitimate saving on the premium path (~¥1,000+ vs walk-in resale). [CN-CHANNEL]
2. **All-Feetech single-bus build (the cheap option, verified 2026-09-27):** legs **6× ST-3215-C018 (12 V)** + wings/neck **4× SC-0043** — both speak the same Feetech **FT-SCS half-duplex TTL protocol**, so all 10 servos share **ONE bus and ONE SDK**. The C018 is rated **4.0–14 V** (OV trip >14 V) → legs run **directly from the 3S pack** (9.9–12.6 V), no leg buck; SC-0043 (3.7–6 V) needs a small 5 V BEC. Servo cost drops ¥6,790 → ≈ **¥1,205 (−82%)**; total BOM ≈ ¥7,523 → ≈ **¥1,940**, at +146 g robot mass. [FTECH-BUILD][CN-BACKUP][STS]
3. ~~Carrier alternative~~ **superseded (2026-09-27):** the robot now uses the owned dev-kit reference carrier at ¥0; the Waveshare IO-BASE-B (¥554, 100×79 mm, 93 g) and the A603 (¥1,400) are no longer purchase candidates. [CARRIER]

### All-Feetech selection & torque re-check (binding at 1.15 kg: hip_roll @2× = 0.91 N·m, hip_pitch/knee ≥0.59 N·m, wings/neck <0.15 N·m)

| Model | Role | Mass | Stall | Voltage | Protocol | ¥ Sep 2026 | hip_roll / knee / wings |
|---|---|---|---|---|---|---|---|
| ST-3215-**C018** (30 kg·cm @12 V) | legs ×6 | 55 g | **2.94 N·m @12 V**; ≈2.72 @11.1 V [LIN]; ≈1.47 @6 V [LIN] | **4.0–14 V** (OV >14 V) | FT-SCS TTL, ID0–253, 38400–1 Mbps | **¥118.50 现货 (1688)**; ¥109–129 [EST] | **PASS 3.0×** / PASS / overkill |
| SC-0043-C001 (coreless) | wings/neck ×4 | **6.6 g** | 2.2 kg·cm @6 V = **0.216 N·m** | 3.7–6 V | FT-SCS TTL, **38400–500 kbps** | ¥45–70 [EST] | — / — / **PASS 1.4×** |
| ST-3032 (middle try) | legs? | 20 g | 0.44 @6 V | ~5–7 V [EST] | FT-SCS TTL | ¥40–60 [EST] | FAIL (49%) / FAIL (75%) / PASS |
| STS3045M (middle try) | legs? | 34.8 g | 0.59 @6 V | 6 V | FT-SCS TTL | ¥60–90 [EST] | FAIL (66%) / MARGINAL / PASS |
| ST-3009 (brushless, middle try) | legs? | 45 g | 1.13 @7.4 V (0.88 @6 V) | 6–7.4 V | FT-SCS TTL | ¥100–150 [EST] | PASS only @7.4 V / PASS / heavy |
| HiWonder LX-16A | legs? | ~50 g [EST] | 1.67–1.96 @6–7.4 V | 6–7.4 V | FT-SCS-derived | ¥99–139 [EST] | PASS / PASS / heavy |

**Middle-weight finding (explicit):** no Feetech or other domestic serial-bus TTL servo in the **20–40 g class clears ≥1.0 N·m** as of Sep 2026. ST-3032 (20 g) fails knee; STS3045M (34.8 g) fails hip_roll; the lightest leg-capable servo is **ST-3009 at 45 g** — but it needs a **7.4 V rail** (extra buck from 3S), costs ≈ the C018, and saves only ~60 g over six legs → **dominated; the middle path is not recommended.** HiWonder LX-16A is torque-correct but 50 g-class and same price as C018 — no advantage. [FTECH-BUILD]

### Costed all-Feetech purchase list (domestic, Sep 2026)

| # | Part | Qty | Unit ¥ | ¥ | Mass (g) | Store link |
|---|---|---|---|---|---|---|
| 1 | Feetech ST-3215-C018 (legs) | 6 | 118.5 | 711 | 330 | [微雪·ST3215商品页](https://www.waveshare.com/product/st3215-servo.htm) · [淘宝搜索 ST3215 30kg 12V](https://s.taobao.com/search?q=ST3215%2030kg%2012V%20%E4%B8%B2%E8%A1%8C%E6%80%BB%E7%BA%BF%E8%88%B5%E6%9C%BA) |
| 2 | Feetech SC-0043-C001 (wings/neck) | 4 | 55 [EST] | 220 | 26 | [飞特·官方商品页](https://www.feetech.cn/en/559569) · [淘宝搜索 飞特 SC-0043](https://s.taobao.com/search?q=%E9%A3%9E%E7%89%B9%20SC-0043%20%E5%BE%AE%E5%9E%8B%E4%B8%B2%E8%A1%8C%E6%80%BB%E7%BA%BF%E8%88%B5%E6%9C%BA) |
| 3 | Spares: C018 ×1 + SC-0043 ×1 | 2 | — | 174 [EST] | 0 | 同上渠道 |
| 4 | Feetech 3-pin bus cables / extensions ~10 pc | 10 | 3 [EST] | 30 | — | [淘宝搜索 飞特 串行总线舵机线](https://s.taobao.com/search?q=%E9%A3%9E%E7%89%B9%20%E4%B8%B2%E8%A1%8C%E6%80%BB%E7%BA%BF%E8%88%B5%E6%9C%BA%E7%BA%BF) |
| 5 | 5 V BEC ≥3 A (wings/neck rail) | 1 | 20 [EST] | 20 | 15 [EST] | [淘宝搜索 5V 3A BEC 降压](https://s.taobao.com/search?q=5V%203A%20BEC%20%E5%8E%8B%E9%99%8D) |
| 6 | SN74LVC1G126 ×5 (bus transceiver) | 5 | 1 | 5 | ~0 | [立创商城搜索 SN74LVC1G126](https://www.szlcsc.com/search?q=SN74LVC1G126) |
| 7 | Feetech URT-1/URT-2 bench adapter | 1 | 45 | 45 | 0 (bench) | [淘宝搜索 飞特 URT-1](https://s.taobao.com/search?q=%E9%A3%9E%E7%89%B9%20URT-1%20%E8%B0%83%E8%AF%95%E6%9D%BF) |
| | **Servo+bus subtotal** | | | **≈ ¥1,205** | **356 (+146)** | |
| | **Full robot BOM (servo swap only; rest of §6 unchanged)** | | | **≈ ¥1,940** | **≈ 1,154 g ≈ 1.15 kg** | |

### Power & bus (one battery, one signal bus)

- One 3S pack feeds **both** the reference carrier (9–20 V barrel) and the servos. Legs (C018, 4–14 V) take **11.1 V direct**; wings/neck (SC-0043, max 6 V) take **5 V from the BEC** — one battery, no leg buck, only one small second rail.
- **One half-duplex TTL signal bus** for all 10 servos (same FT-SCS packet family). The 3-pin chains carry Vcc on pin 2, so power is fed by **taps**: leg segment fed at 3S, wing/neck segment fed at 5 V, SIG+GND continuous end-to-end → one Orin UART + one SN74LVC1G126 + one `feetech-servo-sdk`. If power-split signal integrity proves troublesome on the bench, the conservative fallback is **two buses** (2× UART + 2× transceiver, two power rails cleanly separated).
- Bus baud: run the mixed family at **115200–500 kbps** (SC-0043 caps at 500 k); 500 kbps preferred — a 10-servo sync cycle is ≈3–4 ms, well inside the 20 ms (50 Hz) budget. Re-flash C018 down from its 1 Mbps default. Voltage drop at 11.1 V is forgiving (0.5 V drop → 10.6 V, still in the 4–14 V window); keep chains ≤60 cm, 22 AWG, 2200 µF bulk cap.
- Cables: Feetech standard 3-pin bus cable (JST-family; usually included per servo; extensions ¥2–5 [EST]).

### Software (principle)

The **MuJoCo + PPO pipeline and the 50 Hz joint-target interface are unchanged** — only the low-level driver swaps Dynamixel Protocol-2.0 for the **Feetech SDK** (`sync_write` + `sync_read` exist in FT-SCS; servos reply in order on the broadcast). **Position + load readback confirmed** for the sim2real loop: ST3215 exposes Load / Position / Speed / Input Voltage / Current / Temperature; SC-0043 exposes pos / speed / load. Bench: FE-URT-2 / URT-1 (auto-direction, up to 1 Mbps). Quirks: factory default ID=1 on every unit (assign unique IDs one at a time first); 8-bit checksum, no byte-stuffing (parse by length field); brushless ST-3009 can throw CRC errors (not used in the recommended build). [FTECH-BUILD]

### Comparison — Dynamixel premium vs All-Feetech (Sep 2026, both all-domestic)

| Dimension | Dynamixel premium (6× XC330 + 4× XL330) | All-Feetech (6× C018 + 4× SC-0043) |
|---|---|---|
| Servo ¥ incl. spares | ¥6,790 | ≈ ¥1,205 (−82%) |
| **Total BOM ¥** | **≈ ¥7,523** | **≈ ¥1,940** |
| Servo mass | 210 g | 356 g (+146 g) |
| **Robot mass** | **≈ 1.01 kg** | **≈ 1.15 kg** |
| hip_roll @2× | req 0.79 N·m → XC330 1.10 N·m @6 V **PASS 1.39×** | req 0.91 N·m → C018 ≈2.72 N·m @11.1 V **PASS 3.0×** |
| Buses / protocol | 1 × Dynamixel P2.0 @1 Mbps | 1 × Feetech FT-SCS @500 kbps (power taps) |
| Rails | 1 × 6.0 V (UBEC) | legs 3S direct + 5 V BEC |
| Tooling | Dynamixel SDK / Wizard 2.0 (U2D2 optional) | Feetech SDK / URT-1 (already in §6) |
| Feedback for sim2real | pos / vel / current | pos / load (+V/current on C018) |
| Reliability | proven (microduck, OpenDuck Mini) | STS3215 proven in OpenDuck Mini; C018+SC-0043 mixed bus needs a bench enumeration check |

### Recommendation & decisions

**Recommendation:** if servo cost is the binding constraint, the **all-Feetech build (C018 legs + SC-0043 wings) is torque-safe (3.0× on the binding joint), single-bus, single-battery, ≈¥1,940 total** — the sensible cheap path; lower cost is its advantage, at +146 g mass and a smaller ecosystem. If mass and ecosystem matter more, **keep the Dynamixel build (≈¥7,523 / 1.01 kg / proven)**. The middle path (ST-3009) is not worth the extra rail complexity.

**Two decisions for the user:**
1. **Servo family:** Dynamixel premium (≈¥7,523 / 1.01 kg / proven ecosystem) **vs** all-Feetech (≈¥1,940 / 1.15 kg / one FT-SCS bus + Feetech SDK).
2. **If Feetech:** confirm the **one-bus power-tap** layout (legs 3S direct + wings 5 V BEC on one daisy chain) vs the safer **two-bus** split — bench-test mixed-family enumeration at 500 kbps before the full build. Note: SC-0043 live price/stock needs a 旺旺 confirm ([EST]).

---

## 8. Optional / deferred line items (priced, low effort)

| Item | ¥ | Notes |
|---|---|---|
| 5-DOF leg upgrade (hip_yaw + ankle ×2, 4× XC330) | ≈ 3,200 | mirrors microduck exactly; retrain policy with new kinematics |
| Head roll (+1 XL330) | ≈ 238 | crest/tilt expression |
| Beak servo (XL330) | ≈ 238 | microduck drives it daemon-side, outside RL |
| IMX219 8 MP MIPI camera | 35–60 | **reference-carrier CSI (15-pin)** — needs adapter for Pi-style IMX219 |
| 8×8 ToF (e.g. VL53L8CX) | 150–250 [EST] | deferred |
| Speaker/mic + TTS | 50–150 [EST] | deferred |
| Bluetooth gamepad (ShanWan Q34P) | 61 | teleop |
| Tail servo | ≈ 238 | deferred |

---

## 9. Assumed tools

- FDM printer ≥ 220×220 mm bed (Ender-3 class); Bambu 256×256 recommended — 25 cm body shell does **not** fit whole on 220 mm, split along the long axis. PETG, ~0.6 kg filament.
- Soldering iron (JST-EH crimp or solder joints for bus), multimeter, torque-screwdriver for servo horns (M2×6).
- 格氏 B3 balance charger for the 3S pack (CORE purchase, §6); bench: Mean Well LRS-50-5 5 V/10 A PSU.
- Dev-kit bench power: the kit ships without a PSU — power it with a 65 W USB-C PD adapter (easiest) or a 9–20 V DC barrel supply; use 15 W mode on the bench.

---

## 10. Open questions for the user

1. ✅ **CLOSED — dev kit owned and used on the robot.** JD [10149183026930](https://ic-item.jd.com/10149183026930.html). Decision (2026-09-27): the robot carries the **reference carrier + stock active cooler** as they ship in the box — the **A603 is NOT purchased**, and neither is the Waveshare cooler or the NVMe. Tradeoff accepted: the dev-kit carrier is larger/heavier than the A603 (see §2 + CAD/packaging note) but costs ¥0 and is already in hand.
2. **XL330 sourcing tier:** use 智能佳's ¥95 SKU (may need 企业会员, intermittent stock) or WowRobo's ¥238 with 48 h ship? Reconfirm via 旺旺 before ordering.
3. **Leg DOF freeze:** v1 core = 3 DOF/leg (hip_roll + hip_pitch + knee_pitch, 6 servos) as frozen. Microduck's real legs are 5 DOF — accept the +4-servo optional upgrade now or later?
4. **Battery:** 3S 2200 mAh XT60 confirmed as the only LiPo that fits the reference carrier (2S cannot boot it). Charger is now a CORE line (格氏 B3).
5. **Camera connector:** reference carrier uses 15-pin CSI — revisit adapter when vision is added (deferred).

---

## Domestic sourcing guide (item → Chinese keyword → channel → ¥, Sep 2026)

| Item | Exact Chinese search keyword (clickable) | Channel | ¥ (Sep 2026) |
|---|---|---|---|
| A603 carrier (NOT purchased) | [DFRobot A603 载板](https://www.dfrobot.com.cn/goods-3876.html) | 链接仅作参考 — 机器人改用随附 **reference carrier** | 随开发者套件附带 (¥0) |
| Orin Nano module (owned) | — | — | owned |
| Stock active cooler (NOT purchased) | [微雪 Orin FAN PWM 散热](https://www.waveshare.com/orin-fan-pwm.htm) | 链接仅作参考 — 套件自带 **stock NVIDIA active cooler** (pre-mounted) | 随开发者套件附带 (¥0) |
| NVMe (DEFERRED) | [SN740 2242](https://search.jd.com/Search?keyword=SN740%202242&enc=utf-8) | 京东自营 / 淘宝 (仅日后需要时) | DEFERRED — dev kit boots from microSD; ONNX policy is tiny |
| XC330-M288-T | [XC330-M288-T 舵机](https://s.taobao.com/search?q=XC330-M288-T%20%E8%88%B5%E6%9C%BA) / "ROBOTIS XC330 韩国原装正品" | 智能佳机器人 (Taobao/JD) / Taobao resellers | 700–900 [EST] |
| XL330-M288-T | [Dynamixel XL330-M288-T 舵机](https://item.taobao.com/item.htm?id=638117456346) · [WowRobo ¥238](https://item.taobao.com/item.htm?id=929725677792) · [智能佳 JD](https://item.jd.com/10026901343226.html) | 智能佳 Taobao (¥95); WowRobo (¥238) | 95–238 |
| Feetech ST-3215-C018 (alt legs) | [ST3215 30kg 12V 串行总线舵机](https://s.taobao.com/search?q=ST3215%2030kg%2012V%20%E4%B8%B2%E8%A1%8C%E6%80%BB%E7%BA%BF%E8%88%B5%E6%9C%BA) / "微雪 ST3215" | 微雪代理店 / 1688 (现货) | 110–130 [EST] |
| Feetech SC-0043 (alt wings/neck) | [飞特 SC-0043 微型串行总线舵机](https://s.taobao.com/search?q=%E9%A3%9E%E7%89%B9%20SC-0043%20%E5%BE%AE%E5%9E%8B%E4%B8%B2%E8%A1%8C%E6%80%BB%E7%BA%BF%E8%88%B5%E6%9C%BA) | 飞特官方 / 淘宝 | 45–70 [EST] |
| U2D2 (optional bench) | [ROBOTIS U2D2 调试板](https://item.jd.com/10152431689448.html) | 智能佳 JD item 10152431689448 | 250–350 [EST] |
| Feetech URT-1 adapter | [飞特 URT-1 调试板](https://s.taobao.com/search?q=%E9%A3%9E%E7%89%B9%20URT-1%20%E8%B0%83%E8%AF%95%E6%9D%BF) / "USB转485转TTL" | 淘宝 飞特官方 | 30–60 [EST] |
| SN74LVC1G126 | [SN74LVC1G126](https://www.szlcsc.com/search?q=SN74LVC1G126) | LCSC 立创商城 / 淘宝 | 0.5–2/pc |
| JST-EH 3P cables | [JST-EH 3P 舵机线](https://s.taobao.com/search?q=JST-EH%203P%20%E8%88%B5%E6%9C%BA%E7%BA%BF) / "Robot Cable-3P" | 智能佳 / 淘宝 | 2–5/pc |
| FPX330-H101 horns | [FPX330-H101 支架套装](https://s.taobao.com/search?q=FPX330-H101%20%E6%94%AF%E6%9E%B6%E5%A5%97%E8%A3%85) | 淘宝 | 50–80/set (或PETG打印, ¥1) |
| UBEC 10 A | [好盈 UBEC 10A](https://s.taobao.com/search?q=%E5%A5%BD%E7%9B%88%20UBEC%2010A) / "5V 6V 10A 降压模块" | 好盈官方店 / 淘宝 / 1688 | 40–80 [EST] |
| 3S LiPo | [3S 2200mAh 航模锂电池 XT60](https://s.taobao.com/search?q=3S%202200mAh%20%E8%88%AA%E6%A8%A1%E9%94%82%E7%94%B5%E6%B1%A0%20XT60) | 淘宝 / 1688 | 60–120 [EST] |
| Balance charger | [格氏 B3 平衡充](https://s.taobao.com/search?q=%E6%A0%BC%E6%B0%8F%20B3%20%E5%B9%B3%E8%A1%A1%E5%85%85) | 格氏官方店 / 淘宝 | 80–130 [EST] |
| XT60 switch/fuse | [XT60 开关 航模 保险丝座](https://s.taobao.com/search?q=XT60%20%E5%BC%80%E5%85%B3%20%E8%88%AA%E6%A8%A1%20%E4%BF%9D%E9%99%A9%E4%B8%9D%E5%BA%A7) | 淘宝 | 10–25 [EST] |
| Body IMU | [ICM42688P 六轴IMU](https://s.taobao.com/search?q=ICM42688P%20%E5%85%AD%E8%BD%B4IMU) / "GY模块" | 淘宝 | 25–60 [EST] |
| Head IMU (opt) | [MPU6050 模块 GY-521](https://s.taobao.com/search?q=MPU6050%20%E6%A8%A1%E5%9D%97%20GY-521) | 淘宝 | 8–12 |
| PETG | [PolyLite PETG 1kg](https://s.taobao.com/search?q=PolyLite%20PETG%201kg) / "金质 PETG" | PolyMaker官方店 / 淘宝 | 60–90 [EST] |
| Screw kit | [M2 M2.5 M3 螺丝套装 内六角 304](https://s.taobao.com/search?q=M2%20M2.5%20M3%20%E8%9E%BA%E4%B8%9D%E5%A5%97%E8%A3%85%20304) | 淘宝 | 15–35 [EST] |
| Bearings | [MR63ZZ MR84ZZ 微型轴承](https://s.taobao.com/search?q=MR63ZZ%20MR84ZZ%20%E5%BE%AE%E5%9E%8B%E8%BD%B4%E6%89%BF) | 淘宝 | 1–5/pc |
| Sleeving | [编织网管 包线管 3mm](https://s.1688.com/selloffer/offer_search.htm?keywords=%E7%BC%96%E7%BB%87%E7%BD%91%E7%AE%A1%20%E5%8C%85%E7%BA%BF%E7%AE%A1) | 1688 / 淘宝 | 0.5–2/m |

**Explicit flag:** no core line is unsourcable domestically as of 2026-09-27. The A603 / Waveshare cooler / NVMe are removed from the purchase list (owned dev-kit compute stack used instead). Watch items: (1) **XL330/XC330 prices span a wide verified band** (¥95–238 / ¥700–900) — reconfirm via 旺旺 at order time; (2) XC330 listings must be the **-T (TTL)** suffix, never the RS-485 T288 variant; (3) the cheaper Feetech alternative, if adopted, is a **different protocol and bus** — see §7.

---

## 11. Source index

- [XL330] https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/
- [XC330] https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/
- [STS] https://www.feetechrc.com/en/525603.html · datasheet https://www.feetechrc.com/Data/feetechrc/upload/file/20200611/6372749961523760249976542.pdf · protocol: https://deepwiki.com/beam-bots/feetech/3.2-protocol-layer
- [MJCF] https://raw.githubusercontent.com/pollen-robotics/microduck/main/kinematics/assets/alpha/robot_walk.xml
- [ROBOTD-DESIGN] https://raw.githubusercontent.com/pollen-robotics/microduck/main/docs/design/robotd-design.md
- [CONST] https://raw.githubusercontent.com/pollen-robotics/microduck_rl/develop/src/mjlab_microduck/robot/microduck_constants.py
- [RL-README] https://github.com/pollen-robotics/microduck_rl
- [PROG] https://progressiverobot.com/2026/08/27/microduck/ · [KINGY] https://kingy.ai/blog/hugging-face-microduck-physical-ai-robot/
- [ODM] https://github.com/apirrone/Open_Duck_Mini (README, BOM section)
- [CARRIER] A603: https://www.dfrobot.com/product-2806.html · https://www.dfrobot.com.cn/goods-3876.html · datasheet https://files.seeedstudio.com/products/NVIDIA/A603-Carrier-Board-for-Jetsson-Orin-NX-Nano-Datasheet.pdf · Waveshare IO-BASE: https://www.waveshare.com/jetson-orin-io-base-b.htm · module: https://www.mouser.com/pdfDocs/Jetson_Orin_Nano_Series_DS-11105-001_v11.pdf · cooler: https://www.waveshare.com/orin-fan-pwm.htm · NVMe: https://www.sandisk.com/en-ua/products/ssd/internal-ssd/pc-sn740-ssd?sku=SDDPTQD-256G
- [DEVKIT] NVIDIA Carrier Board Spec SP-11324-001 ("The Developer Kit Weighs 0.175kg"; 9–20 V DC jack; 40-pin; M.2 Key-M): https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf · Super kit envelope 103×90.5×34.77 mm (incl. feet/carrier/module/thermal): https://openzeka.com/wp-content/uploads/2024/12/jetson-super-orin-nano-developer-kit-datasheet.pdf · NVIDIA blog (preassembled heatsink+fan in box): https://developer.nvidia.com/blog/develop-ai-powered-robots-smart-vision-systems-and-more-with-nvidia-jetson-orin-nano-developer-kit/ · Mouser dev-kit datasheet: https://www.mouser.com/datasheet/2/744/jetson_orin_nano_developer_kit_datasheet-3137605.pdf · ATS-NVA-3281-C1 heatsink 38.3 g: https://www.qats.com/Product/Heat-Sinks/BGA-Heat-Sink---High-Performance/Device-Specific---NVIDIA/ATS-NVA-3281-C1-R0/3641.aspx · SparkFun (original 100×79×21 envelope): https://www.sparkfun.com/nvidia-jetson-orin-nano-developer-kit.html
- [CN-CHANNEL] 智能佳机器人 (ROBOTIS授权伙伴since 2007): https://bjrobot.jd.com · 淘宝 item 638117456346 (XL330 ¥95) · WowRobo item 929725677792 (XL330 ¥238) · 智能佳 JD item 10026901343226 (XL330) / 10152431689448 (U2D2) · rosrobot.cn · ROBOTIS中国: http://cn.robotis.com / china@robotis.com · ROBOTIS "shop at Taobao" guidance: https://emanual.robotis.com/docs/en/reference/dxl-selection-guide/ · ChinaMicroDuck BOM (verified 2026-09-02): https://github.com/Shiyao-Huang/ChinaMicroDuck/blob/main/06_bom/技术资料包.md · alternative-motor research: https://github.com/Shiyao-Huang/ChinaMicroDuck/blob/main/06_bom/同级电机替代调研.md
- [CN-BACKUP] Feetech URT-1/FE-URT-2: 淘宝 "飞特 URT-1 调试板" · SC-0043/ST-3032: feetechrc.com product pages · 幻尔LX-16A: 幻尔旗舰店 (hiwonder Taobao) · Waveshare ST3215: 微雪旗舰店 · LCSC: https://www.szlcsc.com
- [FTECH-BUILD] ST-3215-C018 datasheet (4–14 V, 30 kg·cm @12 V, feedback rows): https://www.feetech.cn/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf · SC-0043: https://www.feetech.cn/en/559569 · Waveshare ST3215: https://www.waveshare.com/product/st3215-servo.htm · FT-SCS protocol (sync_read/sync_write): http://doc.feetech.cn/#/prodinfodownload?srcType=FT-SCS-Protocol-41ad23fe8a244712ba160b93 · FE-URT-2: https://www.feetech.cn/serial-port-series-steering-gear_50681 · Feetech catalog (ST-3009/STS3045M sweep): https://www.feetechrc.com/products.html
- [SERVO] Jetson UART 4.25 Mbps: https://www.esys.ir/images/img_Item/3029/Files/Jetson-Orin-Nano-Series-Modules-Datasheet_DS-11105-001_v1.5.pdf · OpenRB-150 1 Mbps: https://robotis.us/openrb-150-starter-kit/
- [PERIPH] ICM-42688-P datasheet: https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf · 格氏B3/好盈UBEC/致钛/维特智能：官方旗舰店及淘宝/京东自营 listings compiled 2026-09-27

---

## 12. Estimates register (what is NOT a confirmed price/number)

Module mass (13–30 g), dev-kit board-assembly sub-split (carrier ~100 g / stock cooler ~50–55 g / feet ~10–15 g — the 175 g total is verified), cable mass/price, UBEC mass (45 g) & price (40–80), switch/fuse mass (30 g) & price (10–25), printed-frame mass (230 g), fasteners/horns mass (60 g), IMU breakout mass (4 g) & price (25–60), wiring mass (45 g), XC330 domestic price (¥700–900), XL330 walk-in price (¥150–238; ¥95 is the 智能佳 listed SKU, intermittent/enterprise), FPX330-H101 price (50–80/set), charger price (80–130), LiPo price (60–120), PETG price (60–90), runtime (~1.2–1.5 h), filament usage, C018 price (¥109–130 [EST]; 1688 ¥118.50 现货 verified 2026-09-27), SC-0043 price (¥45–70 [EST]) & bus baud (38400–500 kbps), ST-3009/STS3045M prices ([EST]), 5 V BEC (¥20 [EST], 15 g [EST]), Feetech bus cables (¥2–5 [EST]). All other figures are datasheet/verified-listing values with URLs above. Prices date-stamped 2026-09-27; reconfirm via 旺旺 at checkout.
