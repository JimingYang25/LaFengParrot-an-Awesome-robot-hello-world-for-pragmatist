"""Audit whether apparent forward motion is stepping or foot sliding."""
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
    parser.add_argument("--harness", type=float, default=0.0)
    parser.add_argument("--reference", action="store_true")
    args = parser.parse_args()

    robot = LaFengParrotGaitEnv(harness_strength=args.harness)
    if args.reference:
        env = None
        model = None
        obs, _ = robot.reset(seed=0)
    else:
        vector = DummyVecEnv([lambda: Monitor(robot)])
        env = VecNormalize.load(RUN_DIR / "vecnormalize.pkl", vector)
        env.training = False
        env.norm_reward = False
        model = PPO.load(
            RUN_DIR / "gait_ppo_final.zip",
            env=env,
            device="cpu",
        )
        obs = env.reset()
    start_trunk_x = float(robot.data.qpos[0])
    previous_event = robot.gait_event_state
    touchdown_x = {"L": [], "R": []}
    contact_slip_distance = {"L": [], "R": []}
    leads = {"L": [], "R": []}

    for step in range(900):
        if args.reference:
            action = np.zeros(robot.action_space.shape, dtype=np.float32)
            obs, _, terminated, truncated, info = robot.step(action)
            done = terminated or truncated
        else:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, dones, infos = env.step(action)
            info = infos[0]
            done = bool(dones[0])
        event = int(info["gait_event"])
        foot_x = {
            "L": float(robot.data.geom_xpos[robot.sole_center_ids[0], 0]),
            "R": float(robot.data.geom_xpos[robot.sole_center_ids[1], 0]),
        }

        if event != previous_event:
            if previous_event == 0 and event == 1:
                print(
                    f"step={step:3d} LEFT liftoff   x={foot_x['L']:+.4f}"
                )
            elif previous_event == 1 and event == 2:
                touchdown_x["L"].append(foot_x["L"])
                leads["L"].append(foot_x["L"] - foot_x["R"])
                print(
                    f"step={step:3d} LEFT touchdown x={foot_x['L']:+.4f} "
                    f"lead={leads['L'][-1] * 1000:+.1f} mm"
                )
            elif previous_event == 2 and event == 3:
                print(
                    f"step={step:3d} RIGHT liftoff  x={foot_x['R']:+.4f}"
                )
            elif previous_event == 3 and event == 0:
                touchdown_x["R"].append(foot_x["R"])
                leads["R"].append(foot_x["R"] - foot_x["L"])
                contact_slip_distance["L"].append(
                    float(info["last_left_cycle_slip"])
                )
                contact_slip_distance["R"].append(
                    float(info["last_right_cycle_slip"])
                )
                print(
                    f"step={step:3d} RIGHT touchdown x={foot_x['R']:+.4f} "
                    f"lead={leads['R'][-1] * 1000:+.1f} mm "
                    f"slip=({contact_slip_distance['L'][-1] * 1000:.1f},"
                    f"{contact_slip_distance['R'][-1] * 1000:.1f}) mm"
                )
            previous_event = event

        if done:
            break

    trunk_distance = float(info["distance"])
    all_slip = contact_slip_distance["L"] + contact_slip_distance["R"]
    all_leads = leads["L"] + leads["R"]
    footprint_advances = []
    for side in ("L", "R"):
        footprint_advances.extend(np.diff(touchdown_x[side]).tolist())

    print("\nGait validity audit")
    print(
        "Stopped by: "
        f"invalid_touchdown={info.get('invalid_touchdown', False)} "
        f"event_timeout={info.get('event_timeout', False)} "
        f"height={info.get('height', float('nan')):.3f} "
        f"upright={info.get('upright', float('nan')):.3f}"
    )
    print(f"Trunk displacement: {trunk_distance:+.4f} m")
    print(f"Completed cycles: {info['completed_cycles']}")
    print(
        "Mean same-foot footprint advance: "
        f"{np.mean(footprint_advances) * 1000:+.1f} mm"
        if footprint_advances else "Mean same-foot footprint advance: unavailable"
    )
    if all_slip:
        print(
            f"Mean integrated contact skid: {np.mean(all_slip) * 1000:.1f} mm"
        )
        print(
            f"Worst integrated contact skid: {np.max(all_slip) * 1000:.1f} mm"
        )
    else:
        print("Integrated contact skid: unavailable")
    print(
        f"Mean touchdown lead: {np.mean(all_leads) * 1000:+.1f} mm"
        if all_leads else "Mean touchdown lead: unavailable"
    )
    valid = bool(
        len(touchdown_x["L"]) >= 2
        and len(touchdown_x["R"]) >= 2
        and np.mean(footprint_advances) > 0.005
        and bool(all_slip)
        and np.max(all_slip) <= 0.008
        and min(all_leads) > 0.003
    )
    print("VALID FORWARD FOOTSTEP GAIT:", valid)
    if env is not None:
        env.close()
    else:
        robot.close()


if __name__ == "__main__":
    main()
