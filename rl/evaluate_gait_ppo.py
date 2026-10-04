"""Evaluate the physically validated walking PPO without assistance."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


RUN_DIR = ROOT / "rl" / "runs" / "gait_ppo_v3_valid"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--harness", type=float, default=0.0)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    base_env = DummyVecEnv(
        [
            lambda: Monitor(
                LaFengParrotGaitEnv(harness_strength=args.harness)
            )
        ]
    )
    env = VecNormalize.load(RUN_DIR / "vecnormalize.pkl", base_env)
    env.training = False
    env.norm_reward = False
    model = PPO.load(
        RUN_DIR / "gait_ppo_final.zip",
        env=env,
        device=args.device,
    )

    passed = 0
    distances = []
    for episode in range(args.episodes):
        obs = env.reset()
        info = {}
        terminated = False
        for step in range(1000):
            action, _ = model.predict(obs, deterministic=True)
            obs, _, dones, infos = env.step(action)
            info = infos[0]
            if dones[0]:
                terminated = not bool(info.get("TimeLimit.truncated", False))
                break

        cycles = int(info.get("completed_cycles", 0))
        forward_cycles = int(info.get("successful_cycles", 0))
        distance = float(info.get("distance", 0.0))
        episode_passed = bool(
            not terminated and cycles >= 4 and forward_cycles == cycles
            and distance >= 0.08
        )
        passed += int(episode_passed)
        distances.append(distance)
        print(
            f"episode={episode:2d} steps={step + 1:4d} "
            f"distance={distance:+.3f}m cycles={cycles} "
            f"forward_cycles={forward_cycles} "
            f"passed={episode_passed}"
        )

    print("\nUnassisted gait evaluation" if args.harness == 0 else "\nAssisted gait evaluation")
    print(f"Passed: {passed}/{args.episodes}")
    print(f"Mean distance: {np.mean(distances):+.3f} m")
    env.close()


if __name__ == "__main__":
    main()
