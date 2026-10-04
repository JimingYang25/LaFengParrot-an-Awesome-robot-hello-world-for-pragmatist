# Policy development and tuning

This guide is for developers who want to fine-tune the included PPO policy,
change the locomotion task, or connect a different reinforcement-learning
algorithm to LaFengParrot.

The repository is a starting point, not a graduated walking controller. The
included checkpoint is usable with a training harness strength of `0.08`, but
it has not passed the assisted 20/20 gate or the unassisted (`0.00`)
graduation gate. Foot-to-floor and foot-to-foot contacts are classified
separately and covered by regression tests.

## 1. Reproduce the baseline first

Install the dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

Validate the generated MuJoCo model:

```bash
python robot_description/make_mjcf.py
python robot_description/verify_mjcf.py
```

Evaluate and view the shipped checkpoint at its verified harness level:

```bash
python -m unittest -v tests.test_gait_contacts
python rl/evaluate_gait_ppo.py --episodes 20 --harness 0.08 --device cpu
python rl/watch_gait_policy.py --harness 0.08 --device cpu
```

Expected baseline for seeds `126..145`: 19/20 episodes pass, no episode has a
cross-foot contact, and seed `141` ends in an early startup balance failure.
Do not begin tuning until the model verifier, contact tests, and this baseline
are reproducible.

## 2. Understand the policy contract

The gait task is implemented in
[`rl/lafengparrot_gait_env.py`](../rl/lafengparrot_gait_env.py). It is a
residual controller: a phase-driven reference trajectory supplies the nominal
leg targets, and the policy adds bounded corrections every 20 ms.

```text
joint target = reference trajectory + filtered policy action * residual scale
```

### Observation

The observation contains 60 normalized values:

- 41 standing-state values: base height and orientation, ten joint positions,
  sixteen velocities, and the previous ten filtered actions.
- Two gait-clock values: sine and cosine of phase.
- Four foot position values: X/Z for the left and right feet.
- Four foot velocity values: X/Z for the left and right feet.
- Two measured contact flags.
- Two contact-point slip speeds.
- Four gait-event one-hot values.
- One current harness-strength value.

Global X/Y position is intentionally excluded so the policy does not depend on
where the robot happens to be in the world.

### Action

The action space is a ten-value `Box(-1, 1)`. The current gait controller uses
policy corrections on six leg joints:

| Action | Joint | Maximum residual correction |
| ---: | --- | ---: |
| 0 | `hip_roll_L` | +/-8 degrees |
| 1 | `hip_roll_R` | +/-8 degrees |
| 2 | `hip_pitch_L` | +/-18 degrees |
| 3 | `hip_pitch_R` | +/-18 degrees |
| 4 | `knee_L` | +/-20 degrees |
| 5 | `knee_R` | +/-20 degrees |
| 6-9 | Wings and neck | Disabled for gait (`0` scale) |

Actions are low-pass filtered as `0.8 * previous + 0.2 * new`. Changing the
action order, observation order, or observation size makes the shipped model
and `vecnormalize.pkl` incompatible unless their weights/statistics are
migrated deliberately.

### Harness

The training harness applies lateral stabilization and corrective body torque.
It never applies forward force. `1.0` is maximum training assistance and `0.0`
is fully unassisted. Treat harness reduction as a curriculum, not a reward
setting to change abruptly.

## 3. Use the environment with another algorithm

`LaFengParrotGaitEnv` follows the Gymnasium API, so it can be connected to
another RL library or a custom control loop:

```python
import numpy as np

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv

env = LaFengParrotGaitEnv(
    target_speed=0.025,
    harness_strength=0.50,
    reset_noise_scale=0.25,
)

obs, info = env.reset(seed=0)
for _ in range(1000):
    action = np.zeros(env.action_space.shape, dtype=np.float32)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break

env.close()
```

For learned policies, normalize observations and preserve the normalization
statistics alongside every checkpoint. During evaluation, freeze observation
statistics and disable reward normalization.

## 4. Fine-tune the shipped PPO baseline

Create an experiment branch before training because the trainer writes its
final model back to `rl/runs/gait_ppo_v3_valid/`:

```bash
git switch -c policy/my-experiment
```

First stabilize any reward or environment change without reducing assistance:

```bash
python rl/train_gait_ppo.py \
  --resume \
  --quiet \
  --steps 200000 \
  --envs 8 \
  --reset-noise-scale 0.25 \
  --learning-rate 0.00005 \
  --start-harness 0.08 \
  --end-harness 0.08 \
  --device cuda
```

Re-evaluate at `0.08`. Only after reaching 20/20 with zero cross-foot contacts
should assistance be reduced. Use a slow stage rather than a jump:

```bash
python rl/train_gait_ppo.py \
  --resume \
  --quiet \
  --steps 1200000 \
  --envs 16 \
  --start-harness 0.08 \
  --end-harness 0.07 \
  --decay-fraction 1.0 \
  --device cuda
```

Then run:

```bash
python rl/evaluate_gait_ppo.py --episodes 10 --harness 0.07 --device cpu
python rl/analyze_gait_policy.py --harness 0.07
python rl/analyze_gait_actions.py 0.07
```

If the pass rate regresses, restore the last passing checkpoint rather than
continuing from a degraded policy. Keep the model ZIP and its matching
`vecnormalize.pkl` together.

The non-resume path in `train_gait_ppo.py` transfers weights and normalization
from `rl/runs/stand_ppo_rocker32/`. Those older standing artifacts are not
included in this repository. Public users should therefore fine-tune the
included gait checkpoint with `--resume`, or replace the standing-transfer
calls with an explicit initialization strategy in their own trainer.

## 5. Main tuning controls

Change one group at a time and record the commit, seed, harness schedule, and
evaluation results.

| Control | Location | Effect and risk |
| --- | --- | --- |
| Target speed | `--speed` | Changes the commanded forward-speed target. Increase gradually. |
| Harness schedule | `--start-harness`, `--end-harness`, `--decay-fraction` | Controls curriculum difficulty. Large jumps commonly destroy a passing gait. |
| Reference motion | `REFERENCE_KNOTS` | Changes lift, swing, touchdown, and double-support timing. Verify contact order after editing. |
| Gait frequency | `gait_frequency` | Changes cadence. Faster is not automatically more stable or faster forward. |
| Leg authority | `residual_scale` | Larger values permit recovery but also increase saturation and violent motion. |
| Initial-state difficulty | `--reset-noise-scale` | Improves robustness when raised gradually. |
| Resume learning rate | `--learning-rate` | Lower values reduce policy drift during narrow robustness refinements. |
| Reward terms | `step()` reward expression | Can change the learned behavior completely; validate physical metrics, not reward alone. |
| PPO optimization | `PPO(...)` in `train_gait_ppo.py` | Tune learning rate, rollout length, batch size, entropy, and network size conservatively. |

Monitor PPO training with:

```bash
tensorboard --logdir rl/runs/gait_ppo_v3_valid/tensorboard --port 6006
```

MuJoCo simulation remains primarily CPU-bound. CUDA accelerates the neural
network updates, while parallel environments increase simulation throughput.
More environments are useful only while the CPU can keep them supplied.

## 6. Evaluate physical behavior, not only reward

The provided evaluator marks an episode as passed only when:

- It does not terminate early.
- It completes at least four gait cycles.
- Every completed cycle is classified as a successful forward cycle.
- Trunk displacement is at least 0.08 m.
- No left/right sole collision occurs, even momentarily.

The gait audit additionally requires:

- Mean same-foot footprint advance above 5 mm.
- Worst integrated contact skid no greater than 8 mm.
- Every recorded touchdown lead above 3 mm.

A candidate graduates only after 20/20 deterministic episodes at harness
`0.00`, followed by visual inspection and action-saturation review. A policy
that stands on one leg, marches in place, slides its feet, or depends on the
harness has not graduated.

## 7. Contact-safety implementation

`_contacts_now()` reports a stance contact only for a sole-versus-floor pair.
Left/right sole contacts are counted independently, penalized immediately,
and terminate an episode when they persist for three control steps. The
evaluator is stricter: even one cross-foot contact makes the episode fail. A
lateral-separation term discourages leg crossing before collision.

The regression tests include a captured crossed-foot configuration lifted
above the floor. This verifies that self-collision is detected without being
misreported as ground contact or contact slip:

```bash
python -m unittest -v tests.test_gait_contacts
```

Keep physical collision enabled. The real robot cannot pass one foot through
the other, and disabling collision would invalidate the gait result.

## 8. Contribution workflow

Keep each change focused and make its result reproducible:

```bash
git switch -c policy/short-description
git add <changed-files>
git commit -m "Describe the policy change"
git push -u origin policy/short-description
gh pr create --base main
```

Include the training seed, steps, harness schedule, pass rate, mean distance,
gait-audit output, and a short video when opening a pull request. For deeper
hardware, RL, deployment, or research collaboration, contact
[2132720978@qq.com](mailto:2132720978@qq.com).
