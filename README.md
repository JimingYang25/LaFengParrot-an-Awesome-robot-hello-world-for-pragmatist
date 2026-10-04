# LaFengParrot

LaFengParrot is a 3D-printable, Jetson-powered parrot table robot with a
MuJoCo model and a reinforcement-learning locomotion stack. The mechanical
design targets a Jetson Orin Nano Super 8 GB and commonly available parts.

## Current status

- MuJoCo model: 10 actuators and a floating base; stable passive standing.
- Controller: PPO residual policy around an alternating six-joint leg reference.
- Verified checkpoint: `h008`, evaluated with 8% training-harness strength.
- Verified result: 10/10 gait episodes, about 0.56 m forward travel per 20 s.
- Graduation target: harness `0.00` and 20/20 strict evaluation episodes.
- Known issue: occasional left/right sole self-contact is currently interpreted
  as ground contact. Fix this before reducing the harness below 0.08.

The harness provides only lateral and attitude stabilization. It applies no
forward force, so forward travel must come from the robot's gait.

## Repository layout

| Path | Contents |
| --- | --- |
| `CAD/` | Parametric Python CAD sources, assembly notes, drawings, STL and STEP exports |
| `robot_description/` | MJCF, URDF, USD, meshes, kinematics and verification tools |
| `rl/` | Gymnasium environments, PPO training, evaluation and policy viewers |
| `BOM.md` | Bill of materials and component notes |

## Verified development environment

- Windows with WSL2 Ubuntu 24.04
- Python 3.12 in a Conda environment
- MuJoCo 3.14.0
- Gymnasium 1.3.0
- Stable-Baselines3 2.9.0
- PyTorch 2.14.0 with CUDA 13.0

The saved policy uses a 60-value normalized observation, separate two-layer
`256 x 256` actor and critic networks, and a 10-value action vector. Only the
six leg residuals currently affect the walking command; wings and neck remain
at their reference positions.

## Validate the robot model

From WSL2:

```bash
cd /mnt/d/Desktop/LaFengParrot/robot_description
python make_mjcf.py
python verify_mjcf.py
```

## Watch the current policy

```bash
cd /mnt/d/Desktop/LaFengParrot
python rl/watch_gait_policy.py --harness 0.08
```

`--harness 0.00` is an experimental unassisted preview. The current checkpoint
has not yet passed the graduation test at that setting.

## Evaluate the checkpoint

```bash
cd /mnt/d/Desktop/LaFengParrot
python rl/evaluate_gait_ppo.py --episodes 10 --harness 0.08 --device cpu
```

The repository retains `rl/runs/gait_ppo_v3_valid/gait_ppo_final.zip` and its
`vecnormalize.pkl`. Intermediate checkpoints, TensorBoard logs, Python caches,
MuJoCo crash logs, and large generated SVG drawings are intentionally ignored.

## Next milestone

1. Restrict ground-contact detection to sole-versus-floor contacts.
2. Detect and penalize left/right foot collisions separately.
3. Add lateral foot-separation feedback.
4. Retrain from `h008` and gradually anneal the harness to zero.

## License

No license has been selected yet. All rights are reserved unless a license is
added later.
