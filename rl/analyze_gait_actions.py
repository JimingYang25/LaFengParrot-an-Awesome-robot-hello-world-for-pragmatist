"""Report deterministic policy action saturation by actuator."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import mujoco
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


def main():
    harness = float(sys.argv[1]) if len(sys.argv) > 1 else 0.24
    run_dir = ROOT / "rl" / "runs" / "gait_ppo_v3_valid"
    robot = LaFengParrotGaitEnv(harness_strength=harness)
    vector = DummyVecEnv([lambda: Monitor(robot)])
    env = VecNormalize.load(run_dir / "vecnormalize.pkl", vector)
    env.training = False
    env.norm_reward = False
    model = PPO.load(run_dir / "gait_ppo_final.zip", env=env, device="cpu")
    obs = env.reset()
    actions = []
    for _ in range(1000):
        action, _ = model.predict(obs, deterministic=True)
        actions.append(action[0].copy())
        obs, _, done, _ = env.step(action)
        if done[0]:
            break
    actions = np.asarray(actions)
    print(f"harness={harness:.2f} steps={len(actions)}")
    actuator_names = [
        mujoco.mj_id2name(robot.model, mujoco.mjtObj.mjOBJ_ACTUATOR, index)
        for index in range(robot.model.nu)
    ]
    for index, name in enumerate(actuator_names):
        values = actions[:, index]
        print(
            f"{name:16s} min={values.min():+.3f} max={values.max():+.3f} "
            f"mean={values.mean():+.3f} std={values.std():.3f} "
            f"near_limit={np.mean(np.abs(values) > 0.95):.1%}"
        )
    env.close()


if __name__ == "__main__":
    main()
