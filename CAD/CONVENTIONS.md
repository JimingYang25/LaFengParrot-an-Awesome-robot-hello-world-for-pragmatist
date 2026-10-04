# LaFengParrot CAD — Conventions & Interfaces (FROZEN 2026-09-27)

This file is the contract every CAD module builds against. Do not deviate silently; if a convention is wrong, change this file and notify the other agents.

## 1. Paths (all Windows, absolute)



* CAD root: the repository-relative `CAD/` directory

* `dims\dimensions.json` + `dims\dimensions.md` — the ONLY source of truth for hardware dimensions (produced by the dimension-research agent; every number has `verified: true/false` and a `source` URL).

* `source\lib\` — hardware solid builders (servos, carrier, battery, power, fasteners, bearings). Pure functions: no frame/trunk design here.

* `source\frame\` — robot structural parts (trunk, legs, wings, neck, head, mounts, panels).

* `source\assembly\` — poses, full-assembly build, clash checks, drawings/export scripts.

* `exports\step\`, `exports\stl\`, `drawings\` — outputs.

* `ASSEMBLY.md` — part tree ↔ BOM mapping, dimension table, fastener list, cable routing, joint axes/zero poses.

## 2. Units & coordinate frame



* Units: **millimeters** everywhere. Mass in grams (metadata only).

* Global frame (right-handed): **+X forward** (parrot faces +X), **+Y left** (parrot's left), **+Z up**.

* Origin `(0,0,0)`: point on the sagittal plane midway between the two **hip\_roll output axes**, at the height of those axes (this is the "hip plane"). Legs hang below (−Z), trunk above (+Z), neck above trunk.

* Every part module builds in **its own local frame** (sensible local origin, documented in META\["origin\_note"]); the assembly module applies poses to place it.

## 3. Module API (every part file)

Each builder file in `source\lib\` and `source\frame\` exposes exactly:



```
META = {

&#x20; "part\_id": "trunk\_shell",            # unique, snake\_case, matches STL/STEP filenames

&#x20; "name": "Trunk shell (PETG)",

&#x20; "bom\_line": "§2 #9 / §6 #15",        # maps to BOM line(s); "n/a" for hardware

&#x20; "qty": 1,

&#x20; "mass\_g": 230.0,                     # datasheet/estimate

&#x20; "material": "PETG | aluminum | PCB | LiPo | steel",

&#x20; "source\_url": "...",                 # datasheet/listing; "n/a" for designed parts

&#x20; "origin\_note": "local frame: ...",

&#x20; "print\_note": "orientation, supports, split hint (if printed)",

}

def build(cfg=None):

&#x20;   """Return a cq.Solid (or cq.Workplane, callers normalize) of the part

&#x20;   in its local frame. cfg: optional dict for parametric overrides."""

&#x20;   ...
```

Registry: `source\registry.py` provides `all_parts() -> dict[part_id, module]` by importing every module in lib + frame and collecting `META` + `build`. Assembly iterates the registry.

## 4. Hardware dimensions — read ONLY from `dims\dimensions.json`

Frame parts that mount hardware (servo pockets, carrier standoffs, battery tray, hole patterns) MUST take their numbers from `dimensions.json`, never hardcode a dimension that exists in the JSON. The JSON schema (keys per part):



```
{

&#x20; "st3215\_c018": {

&#x20;    "body": {"l": 45.2, "w": 24.7, "h": 35.0},

&#x20;    "mount": {"holes": \[\[x1,y1],\[x2,y2],...], "diameter": 2.2, "screw": "M2"},

&#x20;    "shaft": {"spline": "25T", "outer\_d": 6.0, "length": 6.0, "axis\_dir": "body\_long"},

&#x20;    "horn": {"span": 40.0, "arm\_count": 4, "screw\_holes": "M2"},

&#x20;    "connector": {"type": "JST-PH 3pin", "location": "face\_opposite\_shaft"},

&#x20;    "mass\_g": 55.0,

&#x20;    "source": "\<url>", "verified": true

&#x20; },

&#x20; "sc0043\_c001": {...},

&#x20; "orin\_carrier": {"envelope": \[103,90.5,34.8], "board": \[100,79,1.6],

&#x20;    "mount\_holes": \[\[x,y],...], "mount\_screw": "M2.5",

&#x20;    "connectors": {"barrel": \[x,y], "40pin": \[x,y], "csi1": \[x,y], "csi2": \[x,y],

&#x20;                   "microsd": \[x,y], "usb": \[x,y], "fan\_exhaust": \[x,y]},

&#x20;    "module\_center": \[x,y], "source": "\<url>", "verified": false},

&#x20; "lipo\_3s\_2200": {"size": \[l,w,h], "mass\_g": 185, "connector": "XT60", "balance": "JST-XH", ...},

&#x20; "bec\_5v3a": {...}, "xt60\_switch": {...}, "fuse\_holder": {...},

&#x20; "imuc\_icm42688p": {...}, "bearing\_mr63": {"d":3,"D":6,"B":2.5}, "bearing\_mr84": {"d":4,"D":8,"B":2},

&#x20; "fastener\_m2": {"head\_d":3.8,"head\_h":2.0,"thread":2.0,"clear":2.2},

&#x20; "fastener\_m25": {"head\_d":4.5,"head\_h":2.5,"thread":2.5,"clear":2.7},

&#x20; "fastener\_m3": {"head\_d":5.5,"head\_h":3.0,"thread":3.0,"clear":3.2}

}
```

If a number is missing from the JSON, the frame part uses `[EST]` value from `dimensions.md` and marks it in `META["origin_note"]`. Never invent silently.

## 5. Clearances & print rules (PETG FDM)



* Moving-pair radial fit: shaft-in-bearing / servo-horn-on-shaft → nominal + **0.1–0.2 mm** on the bore, printed in PETG.

* Non-moving press/slip: screw boss bore = thread + 0.1 (self-tap) or clearance per §4 fastener table.

* Face-to-face mating clearance: **0.3–0.5 mm** on mating bosses/tabs.

* Wall thickness: structural walls **≥ 2.0 mm**, servo pockets **≥ 1.6 mm**, cosmetic shell **1.6 mm**.

* Screw bosses: OD = head\_d + 2× wall (min 6.0 mm for M2/M2.5, 6.8 for M3 at 2 mm wall), boss height ≥ 2× screw engagement.

* Print splits: the trunk shell is split (long axis or clamshell) so each printed piece fits ≤ 220×220 mm bed — mark `print_note` with the split; final split decision waits for the user's printer bed (flag, don't block).

* Corner radii ≥ 1 mm on printed parts (avoid stress risers); print orientation note in `print_note` (surfaces that must be dimensionally clean face away from supports).

## 6. Kinematic anchors & joint axes (MUST match the final ASSEMBLY.md and later MuJoCo model)



* **Legs (3 DOF/leg, mirroring microduck scaled to parrot):**


  * hip\_roll: axis ∥ **X** (frontal-plane abduction). Left/right hip\_roll axes separated **54 mm (±27 mm from sagittal, realized)**. Servo: ST-3215-C018, output shaft along X.

  * **CHANGE RECORD (2026-09-27, assembly clash check):** hip half-spacing widened from 34 mm to 52 mm total (planned) and realized at **54 mm (±27)** after the REV-B rebuild. Root cause: the ST-3215-C018 body (45.2×24.7×35, 55 g) makes the hip\_mount housing 50.6 mm wide in Y and the thigh link 38.4 mm wide; at ±17 mm the L/R housings, thigh beams and hip\_roll servo bodies overlap across the sagittal plane (measured 0.6–9.6 cm³ intersections). 54 mm total gives ≥1.5 mm per-side clearance on the widest part. Torque: hip\_roll lever arm r ≈ **33 mm** (half-spacing 27 + 6 mm roll margin) → required @2× = 0.961 N·m at M=1.485 kg vs C018 stall ≈ 2.72 N·m @11.1 V → **PASS with 2.83× margin** (still \~3.0× at the 1.38 kg frame+hardware mass). **MuJoCo kinematics must use 54 mm spacing** (recorded in ASSEMBLY.md).

  * hip\_pitch: axis ∥ **Y** (sagittal swing), located **42 mm** below the hip\_roll axis (thigh length between hip\_pitch output and knee axis).

  * knee\_pitch: axis ∥ **Y**, located **42 mm** below hip\_pitch (thigh link), shin runs **50 mm** from knee axis to ankle/foot (shin link).

  * Foot: small ground-contact pad at shin end, \~10 mm above floor in zero pose; keep CoM low (battery lowest, carrier above).

* **Wings (2 DOF):** one flap DOF each. Axis ∥ **Y** (wings spread sideways ±) — wing servo (SC-0043) mounted at the shoulders, output axis lateral, wing arm extending in the ±Y direction with a printed airfoil-ish flat panel.

* **Neck (2 DOF):** neck\_yaw axis ∥ **Z**, then neck\_pitch axis ∥ **Y**, both stacked above the trunk top, lifting the head \~60–80 mm above the trunk; head shell on top with beak + crest.

* **Zero pose (standing):** trunk vertical; all leg joint angles = 0 (legs straight down); wings level (±Y); neck straight up (yaw=0, pitch=0). The crouched gait (hip\_pitch 26°/knee \~0°) is a *policy* offset, not the CAD zero — record both in ASSEMBLY.md so MuJoCo inherits exact axes.

* **REV B — STABILITY REVISION (2026-09-27, user-directed):**


  * **Foot (in shin\_link, 2026-09-28 rocker update):** fixed compound-rocker sole **40 (X, heel→toe) × 44 (Y, lateral) × 4 mm maximum**, centered on the shin axis. The centre 32 mm is flat at local z = −54; two 2 mm facets per end rise through −53.4 to −52 at heel and toe. It is one printed solid with the shin—**not a wheel and not an extra assembly**. Leg drop remains 138 mm. Lateral inner gap between L/R soles = 10 mm (inner edges at y=±5 with track ±27).

  * **Neck:** neck\_linkage pitch axis lowered **z=70 → z=52** (H\_n = 52 mm, −26%): base+yaw block unchanged (0–25.4), yoke shortened; both SC-0043 servos keep full travel. Head crest falls accordingly (global pitch axis 203 → **185**). Head-pitched-down travel check: head shell front must clear the trunk roof (≥3 mm) at −45° pitch.

  * **Carrier mount (low CoG):** carrier board-top **z=101 → z=72** (realized; feet bottom ≈ 65.4, standoffs ≈ **33 mm \[EST]** from the trunk floor 33; cooler exhaust ≈ 100 with the roof vent at \~131.5 → \~28 mm plenum above; airflow is plenum-style, not direct). Battery tray seated on the trunk floor (base at z=33), battery stays y=−23 low.

  * **Cable stubs:** both servo modules' cosmetic 150 mm cable cylinders shortened to **15 mm** exit stubs (envelope becomes structural: x\[−56,+70], y\[−189,+189], z\[−138,\~250]).

  * **CoM target:** whole-robot CoM height ≤ \~180 mm using real frame mass (456 g PETG at 1.27) + hardware masses (\~1.36 kg total); support-polygon lateral half-base 49 mm (stance outer edge), forward half-base 20 mm; tipping angle = atan(half-base/CoM\_z). These revised dims are what the later MuJoCo model must inherit.

## 7. Assembly & outputs



* `source\assembly\poses.py`: one `def poses() -> dict[part_id, cq.Location]` for the standing pose and `def exploded() -> dict[part_id, cq.Location]` (offsets along ±X/±Y/±Z, ≥ 30 mm apart per direction).

* Full assembly STEP: `exports\step\LaFengParrot_full.STEP`; per-part STEP + STL also exported (STL in local frame, `print_note` gives print orientation — do NOT rotate STLs).

* Drawings (deterministic, from CAD data — NO AI image generation): front (XY), side (YZ) orthographic with key dimensions; exploded isometric. PNG + SVG (+ PDF if convenient). Use matplotlib-based projection of the part solids (or OCP offscreen if working).

* Clash check: pairwise solid intersection volume (OCP `BRepAlgoAPI_Common`) over the standing pose, report any pair with volume > 0.01 mm³; also confirm service access (microSD slot, XT60, barrel jack, 40-pin) is not fully enclosed.

## 8. Reporting

Every agent returns: absolute paths of outputs, the dimension table it used (with verified/EST + URL), fit/clash results, and any dimension it could NOT verify (explicitly marked). Nothing fabricated; unverifiable → \[EST] + flagged.
