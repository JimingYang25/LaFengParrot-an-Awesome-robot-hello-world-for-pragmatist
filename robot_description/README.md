# LaFengParrot — robot_description (REV-B)

Floating-base biped/quadriped-style parrot robot description for RL, generated **from the real
CadQuery CAD** (REV-B) into three mutually consistent formats:

| Format | File | Primary use |
|---|---|---|
| MJCF | `mjcf/lafengparrot.xml` | **PPO training asset (MuJoCo)** — primary |
| URDF | `urdf/lafengparrot.urdf` | PyBullet / ROS / general tooling |
| USD | `usd/lafengparrot.usd` | Isaac Sim / Isaac Lab (PhysX baked) |

All three are generated from **one frozen parameter source** (`kinematics.json`) + the real CAD
solids (meshes + inertials), so kinematic anchors, limits, inertials and contacts agree by
construction. A cross-format checker (`verify_cross.py`) re-asserts this on every run.

---

## 1. Kinematic tree (floating base, 10 actuated joints)

```
trunk (base_link, free joint — floating)
├── hip_roll_L (axis X)  ─ hip_pitch_L (Y) ─ knee_L (Y) ─ shin_L + foot
├── hip_roll_R (axis X)  ─ hip_pitch_R (Y) ─ knee_R (Y) ─ shin_R + foot
├── wing_flap_L (axis Y) ─ wing arm (fixed)
├── wing_flap_R (axis Y) ─ wing arm (fixed)
└── neck_yaw (axis Z) ─ neck_pitch (Y) ─ head
```

- **Servo mapping:** legs = Feetech **ST-3215-C018** (6×, effort 2.72 N·m); wings/neck = Feetech
  **SC-0043-C001** (4×, effort 0.22 N·m). All 10 on one FT-SCS bus in the real robot.
- **Zero pose = standing** (all joints at 0; soles level at global z = −138 mm).
- **Joint limits (deg; [EST] microduck-like):**

| joint | axis | origin (mm, trunk frame) | range |
|---|---|---|---|
| hip_roll L/R | X | (0, ±27, 0) | ±22° |
| hip_pitch L/R | Y | (0, ±27, −42) | ±90° |
| knee L/R | Y | (0, ±27, −84) | 0…150° |
| wing_flap L/R | Y | (0, ±62, 60) | ±45° |
| neck_yaw | Z | (0, 0, 133) | ±90° |
| neck_pitch | Y | (0, 0, 185) | ±45° |

## 2. Joint indexing — READ BEFORE WRITING RL CODE

MuJoCo assigns **qpos/qvel order by tree DFS** (leg-major): `hip_roll_L, hip_pitch_L, knee_L,
hip_roll_R, hip_pitch_R, knee_R, wing_flap_L, wing_flap_R, neck_yaw, neck_pitch` — this is the
correct, stable model order and must NOT be "re-ordered" by restructuring the tree.

The **actuator (ctrl) order is canonical** (kinematics.json order) because actuators bind to
joints by name.

→ Use `joint_name_index_map.json` to map names ↔ indices. **Index observations/actions BY NAME,
never by hard-coded position.**

| index type | layout |
|---|---|
| qpos (17) | 0–2 freejoint trans, 3–6 freejoint quat, 7–16 hinges (DFS order) |
| qvel (16) | 0–5 freejoint (3 trans + 3 rot), 6–15 hinges (DFS order) |
| ctrl (10) | canonical: hip_roll_L, hip_roll_R, hip_pitch_L, hip_pitch_R, knee_L, knee_R, wing_flap_L, wing_flap_R, neck_yaw, neck_pitch |

## 3. How to load

**MJCF (MuJoCo, PPO asset):**
```python
import mujoco
model = mujoco.MjModel.from_xml_path("mjcf/lafengparrot.xml")
data = mujoco.MjData(model)   # nq=17, nv=16, nu=10
```
- Position actuators (joint-target interface, 50 Hz): `ctrl` **in radians**, `ctrlrange` radians.
- Contacts: only the ten fixed sole facets (five per foot) touch the floor; the 32 mm flat
  centres provide standing stability and the raised toe/heel facets permit rollover. These are
  not wheels; visual/hull geoms remain `contype=0`.
  ground friction 1.0; sole friction (0.9, 0.005, 0.0001).
- `imu_trunk` site on the trunk at (0, 0, 0.05).
- Init helper: to start standing with the physical CAD sole on the ground, set the free base z
  so the trunk sits ≈ +0.138 m (the model itself has trunk pos = 0).

**URDF:**
```python
from urdfpy import URDF
r = URDF.load("urdf/lafengparrot.urdf")
```
- PyBullet: `p.loadURDF(..., useFixedBase=False)` — trunk becomes the 6-DOF floating base
  (no world joint needed). **PyBullet could not be installed on this machine (Python 3.14 has
  no wheel; source build fails on missing Python.h) — loading was verified with urdfpy instead
  (11 links / 10 joints, zero-pose FK reproduces all link frame origins with 0 error).**
- ROS: a world→base_link floating joint is added by the loader.

**USD (Isaac):**
```python
from pxr import Usd
stage = Usd.Stage.Open("usd/lafengparrot.usd")
```
- Physics **is baked**: ArticulationRootAPI ×1, RigidBodyAPI ×11, MassAPI ×11 (incl. diagonal
  inertia + principal axes), PhysicsRevoluteJoint ×10, DriveAPI ×10 (kp=40, kv=4, maxForce =
  servo effort), CollisionAPI ×13 (11 hulls + 2 sole cubes), visual UsdGeomMesh ×11.
- metersPerUnit = 1, up = Z. Load directly into Isaac Sim/Lab; joints are resolved by name.
- Drive stiffness/damping is a single set (legs and wings/neck not differentiated) — split per
  joint if needed.

## 4. Meshes & inertials (from the real CAD)

- `meshes/visual/<link>.stl` — tessellated real CadQuery solids (linear deflection 0.4 mm),
  already in each link's frame, **millimeters** (consumers scale: MuJoCo mesh scale="0.001").
- `meshes/collision/<link>_col.stl` — convex hulls for the same bodies.
- MJCF sole contact: five thin box facets per foot follow the 40×44 mm CAD rocker profile;
  the flat centre underside is local z=−54 mm and both ends rise to z=−52 mm.
- `inertials.json` — per-link mass (g), CoM (mm, link frame), inertia (kg·m², about CoM, link axes);
  includes the 105 g fastener/bearing/cable lump [EST] distributed by mass fraction.

**Mass & CoM reconciliation (matches REV-B CAD):**
total **1483.8 g** (target ≈ 1.485 kg) · whole-robot CoM height above floor **162.57 mm**
(target 162.5 mm).

## 5. Verification summary (2026-09-27)

| Check | Result |
|---|---|
| MJCF loads in mujoco | nq=17, nv=16, nu=10; 10/10 ranges; 400-step neutral sim stable, zero warnings, ncon=16; physical sole underside z = −0.1380 |
| Rocker crouch sweep | 0/10/15/20/25/30° knee targets all stable for 8 s; continuous contact; maximum trunk tilt 7.4° |
| URDF parses | urdfpy 11 links / 10 joints; axes+limits 10/10; zero-pose FK error 0.00e+00 m (PyBullet unavailable on Py3.14 — stated) |
| USD opens via pxr | ArticulationRootAPI 1, rigid bodies 11, revolute joints 10, drives 10, collision 13; axes+limits 10/10 |
| Cross-format | `verify_cross.py`: content 10/10 per format; URDF order canonical; MJCF actuator order canonical (qpos DFS documented); USD 10 names present (hierarchy-embedded) → **ALL THREE CONSISTENT** |

## 6. Generation pipeline (re-runnable)

```
CAD (poses.py, registry, dims) + dimensions.json
        └─ generate_meshes.py   → meshes/visual/*.stl, meshes/collision/*_col.stl, inertials.json
kinematics.json (single source)
        ├─ make_mjcf.py  (+ verify_mjcf.py)   → mjcf/lafengparrot.xml
        ├─ make_urdf.py  (+ verify_urdf.py)   → urdf/lafengparrot.urdf
        └─ make_usd.py   (+ verify_usd.py)    → usd/lafengparrot.usd
verify_cross.py   → cross-format consistency
make_name_map.py  → joint_name_index_map.json (from the actual MuJoCo model)
```

## 7. [EST] / limitations (honest list)

- **PyBullet load test skipped**: no Python 3.14 wheel; source build fails (missing Python.h).
  URDF correctness rests on urdfpy parse + FK.
- **Joint damping 0.5, frictionloss 0.05, kp=40, kv=4, armature 0.01 (legs) / 0.002 (wings·neck):
  [EST]** — tunable for PPO.
- **105 g lump** (fasteners/bearings/cables) and its placement: [EST].
- USD drives: single kp/kv set for all 10 joints; split per joint if needed.
- Joint limits are microduck-like estimates; verify against the physical servos (ST-3215 300°/s,
  SC-0043 similar) on first assembly.
- REV-B inherited values are authoritative here: hip rail 54 mm (±27), neck pitch local z 52 /
  global 185, carrier board-top z=72, soles z = −138, 40×44 soles, CoM 162.5 mm.
