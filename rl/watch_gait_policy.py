"""Watch the physically validated forward-step policy in MuJoCo."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mujoco.viewer
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


RUN_DIR = ROOT / "rl" / "runs" / "gait_ppo_v3_valid"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--harness",
        type=float,
        default=0.0,
        help="Keep at 0.0 to view the real unassisted policy.",
    )
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    robot = LaFengParrotGaitEnv(harness_strength=args.harness)
    vector = DummyVecEnv([lambda: Monitor(robot)])
    env = VecNormalize.load(RUN_DIR / "vecnormalize.pkl", vector)
    env.training = False
    env.norm_reward = False
    model = PPO.load(
        RUN_DIR / "gait_ppo_final.zip",
        env=env,
        device=args.device,
    )

    obs = env.reset()
    episode = 0
    old_cycles = 0
    print("Walking-V3 valid-footstep PPO policy")
    print(f"Harness: {args.harness:.2f} (0.00 means completely unassisted)")
    print("Close the viewer or press Ctrl+C to stop.")

    with mujoco.viewer.launch_passive(robot.model, robot.data) as viewer:
        viewer.cam.lookat[:] = [0.0, 0.0, 0.08]
        viewer.cam.distance = 0.80
        viewer.cam.azimuth = 150
        viewer.cam.elevation = -15

        while viewer.is_running():
            frame_start = time.perf_counter()
            action, _ = model.predict(obs, deterministic=True)
            obs, _, dones, infos = env.step(action)
            info = infos[0]

            cycles = int(info.get("completed_cycles", 0))
            if cycles != old_cycles:
                old_cycles = cycles
                print(
                    f"cycle={cycles} "
                    f"forward_cycles={info.get('successful_cycles', 0)} "
                    f"distance={info.get('distance', 0.0):+.3f} m",
                    flush=True,
                )

            # Keep the camera fixed in world coordinates so forward motion is
            # visible instead of being cancelled by a tracking camera.
            viewer.sync()

            if dones[0]:
                episode += 1
                fell = not bool(info.get("TimeLimit.truncated", False))
                print(
                    f"episode={episode} steps={info.get('episode', {}).get('l', 0)} "
                    f"distance={info.get('distance', 0.0):+.3f} m "
                    f"cycles={cycles} "
                    f"forward_cycles={info.get('successful_cycles', 0)} "
                    f"fell={fell}",
                    flush=True,
                )
                old_cycles = 0

            remaining = robot.control_dt - (time.perf_counter() - frame_start)
            if remaining > 0.0:
                time.sleep(remaining)

    env.close()


if __name__ == "__main__":
    main()
