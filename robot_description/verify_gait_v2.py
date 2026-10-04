"""Headless acceptance test for the Walking-V2 alternating reference."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", type=float, default=1.0)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--steps", type=int, default=650)
    args = parser.parse_args()

    passes = 0
    print(
        f"Walking-V2 acceptance: harness={args.harness:.2f}, "
        f"steps={args.steps}"
    )
    print(
        f"{'seed':>4s} {'steps':>5s} {'distance':>9s} "
        f"{'cycles':>7s} {'forward':>7s} {'result':>7s}"
    )
    print("-" * 51)

    for seed in range(args.seeds):
        env = LaFengParrotGaitEnv(harness_strength=args.harness)
        env.reset(seed=seed)
        info = {}
        terminated = truncated = False

        for step in range(args.steps):
            _, _, terminated, truncated, info = env.step(
                np.zeros(env.action_space.shape, dtype=np.float32)
            )
            if terminated or truncated:
                break

        passed = bool(
            not terminated
            and info["completed_cycles"] >= 2
            and info["successful_cycles"] >= 2
            and info["distance"] >= 0.03
        )
        passes += int(passed)
        print(
            f"{seed:4d} {step + 1:5d} {info['distance']:+8.3f}m "
            f"{info['completed_cycles']:7d} "
            f"{info['successful_cycles']:7d} "
            f"{'PASS' if passed else 'FAIL':>7s}"
        )
        env.close()

    required = max(1, int(np.ceil(0.8 * args.seeds)))
    accepted = passes >= required
    print("-" * 51)
    print(f"Passed: {passes}/{args.seeds} (required {required})")
    print("GAIT REFERENCE ACCEPTED:", accepted)
    raise SystemExit(0 if accepted else 1)


if __name__ == "__main__":
    main()
