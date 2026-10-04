# LaFengParrot

LaFengParrot is a 3D-printable, Jetson-powered parrot table robot with a
MuJoCo model and a reinforcement-learning locomotion stack. The mechanical
design targets a Jetson Orin Nano Super 8 GB and commonly available parts.

This repository is an engineering starting point for developers and
researchers who want to design, train, evaluate, and deploy their own robot
policies. It provides a reproducible mechanical and simulation baseline rather
than a finished consumer product.

## Current status
<img width="680" height="440" alt="屏幕录制 2026-10-05 033540" src="https://github.com/user-attachments/assets/1adbbdf9-e6c8-4775-beb8-8d4764a9c03f" />




- MuJoCo model: 10 actuators and a floating base; stable passive standing.
- Controller: PPO residual policy around an alternating six-joint leg reference.
- Verified checkpoint: `h008`, evaluated with 8% training-harness strength.
- Fixed-seed result: 19/20 episodes (`126..145`), zero cross-foot
  contacts, and about 0.54 m mean forward travel per 20 s.
- Graduation target: harness `0.00` and 20/20 strict evaluation episodes.
- Contact safety: floor contact and foot-to-foot collision are classified
  separately; any cross-foot contact fails evaluation.
- Current limitation: seed `141` exposes an early startup balance failure at
  `h008`, so the checkpoint is a development baseline, not a deployable gait.


<img width="880" height="640" alt="exploded" src="https://github.com/user-attachments/assets/67be27cf-9a0d-472f-b9ac-eb9058fd098b" />


The harness provides only lateral and attitude stabilization. It applies no
forward force, so forward travel must come from the robot's gait.

## Repository layout

| Path | Contents |
| --- | --- |
| `CAD/` | Parametric Python CAD sources, assembly notes, drawings, STL and STEP exports |
| `robot_description/` | MJCF, URDF, USD, meshes, kinematics and verification tools |
| `rl/` | Gymnasium environments, PPO training, evaluation and policy viewers |
| `BOM.md` | Bill of materials and component notes |

Policy developers should begin with the
[policy development and tuning guide](docs/POLICY_DEVELOPMENT.md). It explains
the observation/action contract, safe curriculum workflow, tuning controls,
evaluation gates, and how to connect another RL implementation.

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

## Clone the repository

```bash
git clone https://github.com/JimingYang25/LaFengParrot__An-Awesome-starting-point-for-your-policy.git LaFengParrot
cd LaFengParrot
```

All commands below are run from the repository root.

## Install Python dependencies

Python 3.12 is recommended. Create and activate an isolated environment, then
install the tested dependencies:

```bash
python -m pip install -r requirements.txt
```

For CUDA training, install the PyTorch wheel matching the host's CUDA setup
before running the command above. The CUDA-local build version may include a
suffix such as `+cu130`.

## Validate the robot model

From WSL2:

```bash
python robot_description/make_mjcf.py
python robot_description/verify_mjcf.py
```

## Watch the current policy

```bash
python rl/watch_gait_policy.py --harness 0.08
```

`--harness 0.00` is an experimental unassisted preview. The current checkpoint
has not yet passed the graduation test at that setting.

## Evaluate the checkpoint

```bash
python rl/evaluate_gait_ppo.py --episodes 20 --harness 0.08 --device cpu
```

The repository retains `rl/runs/gait_ppo_v3_valid/gait_ppo_final.zip` and its
`vecnormalize.pkl`. Intermediate checkpoints, TensorBoard logs, Python caches,
MuJoCo crash logs, and large generated SVG drawings are intentionally ignored.

## Next milestone

1. Improve startup robustness from 19/20 to 20/20 at harness `0.08`.
2. Gradually anneal the harness to zero without losing the collision gate.
3. Expand reset and push randomization, then repeat fixed-seed evaluation.
4. Validate actuator limits and add a hardware emergency-stop layer before
   transferring any learned policy to the physical robot.

## Collaboration and contact

Bug reports, reproducible experiments, and focused improvements are welcome
through GitHub issues and pull requests. For deeper collaboration involving
robot hardware, reinforcement learning, deployment, or research, contact
[2132720978@qq.com](mailto:2132720978@qq.com).

## License

Copyright 2026 Jiming ([JimingYang25](https://github.com/JimingYang25)).

This project—including its source code, robot descriptions, CAD files, and
documentation—is licensed under the [Apache License 2.0](LICENSE), unless a
file states otherwise.
