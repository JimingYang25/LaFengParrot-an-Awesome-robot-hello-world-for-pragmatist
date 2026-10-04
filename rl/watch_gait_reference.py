"""Visualize the alternating Walking-V2 curriculum reference.

This is not a trained policy. It is the left-right reference motion used to
teach PPO. The training-only balance harness applies no forward force.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mujoco.viewer
import numpy as np

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


EVENT_NAMES = (
    "waiting for LEFT flight",
    "waiting for LEFT touchdown",
    "waiting for RIGHT flight",
    "waiting for RIGHT touchdown",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    env = LaFengParrotGaitEnv(harness_strength=args.harness)
    env.reset(seed=args.seed)
    action = np.zeros(env.action_space.shape, dtype=np.float32)

    print("Walking-V2 alternating reference (not a trained policy)")
    print(f"Training harness: {args.harness:.2f}; forward harness force: 0 N")
    print("A valid cycle requires both feet to fly and touch down in order.")

    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        viewer.cam.lookat[:] = [0.0, 0.0, 0.08]
        viewer.cam.distance = 0.52
        viewer.cam.azimuth = 150
        viewer.cam.elevation = -15

        episode = 0
        old_event = env.gait_event_state
        old_cycles = 0
        while viewer.is_running():
            frame_start = time.perf_counter()
            _, _, terminated, truncated, info = env.step(action)

            if info["gait_event"] != old_event:
                old_event = info["gait_event"]
                print(f"event: {EVENT_NAMES[old_event]}", flush=True)
            if info["completed_cycles"] != old_cycles:
                old_cycles = info["completed_cycles"]
                print(
                    f"cycle={old_cycles} "
                    f"forward_cycles={info['successful_cycles']} "
                    f"distance={info['distance']:+.3f} m",
                    flush=True,
                )

            viewer.cam.lookat[0] = float(env.data.qpos[0])
            viewer.sync()

            if terminated or truncated:
                episode += 1
                print(
                    f"episode={episode} steps={env.elapsed_steps} "
                    f"distance={info['distance']:+.3f} m "
                    f"cycles={info['completed_cycles']} "
                    f"forward_cycles={info['successful_cycles']} "
                    f"fell={terminated and not info['event_timeout']} "
                    f"event_timeout={info['event_timeout']}",
                    flush=True,
                )
                env.reset(seed=args.seed + episode)
                old_event = env.gait_event_state
                old_cycles = 0

            remaining = env.control_dt - (time.perf_counter() - frame_start)
            if remaining > 0.0:
                time.sleep(remaining)

    env.close()


if __name__ == "__main__":
    main()
