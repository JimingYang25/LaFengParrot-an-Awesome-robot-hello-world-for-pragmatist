#!/usr/bin/env python3
"""Dynamic checks for the fixed compound-rocker feet.

The test ramps both legs from the straight standing pose into several
kinematically centred crouches.  It is intentionally deterministic and applies
no external support or hidden weld.  A pass means the new sole keeps a finite,
upright, floor-contacting model while the knee motion rolls onto its facets.
"""
from __future__ import annotations

import math
import os

import mujoco
import numpy as np


HERE = os.path.dirname(os.path.abspath(__file__))
XML = os.path.join(HERE, "mjcf", "lafengparrot.xml")


def balanced_hip_angle(knee_rad: float) -> float:
    """Nominal hip target that places the trunk over the rolled contact patch.

    Merely centring the geometric sole puts the active toe-side facet ahead of
    the centre of mass and creates a backward tipping moment.  The 1.25 ratio
    was verified by a deterministic sweep over 5--30 degree knee crouches.
    """
    return -1.25 * knee_rad


def actuator_id(model: mujoco.MjModel, name: str) -> int:
    return mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)


def run_trial(model: mujoco.MjModel, knee_deg: float) -> dict:
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)
    data.qpos[2] = 0.138
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)

    hip = balanced_hip_angle(math.radians(knee_deg))
    knee = math.radians(knee_deg)
    targets = {
        "hip_pitch_L": hip,
        "hip_pitch_R": hip,
        "knee_L": knee,
        "knee_R": knee,
    }
    ids = {name: actuator_id(model, name) for name in targets}

    trunk_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk")
    ramp_s, hold_s = 2.0, 6.0
    steps = int((ramp_s + hold_s) / model.opt.timestep)
    min_height = float(data.qpos[2])
    min_upright = 1.0
    min_contacts_after_ramp = 10**9
    max_contacts = 0
    finite = True

    for step in range(steps):
        t = step * model.opt.timestep
        blend = min(1.0, t / ramp_s)
        # Smoothstep avoids an impulse at the start/end of the pose change.
        blend = blend * blend * (3.0 - 2.0 * blend)
        for name, target in targets.items():
            data.ctrl[ids[name]] = blend * target

        mujoco.mj_step(model, data)
        finite = finite and bool(
            np.all(np.isfinite(data.qpos)) and np.all(np.isfinite(data.qvel))
        )
        min_height = min(min_height, float(data.qpos[2]))
        upright = float(data.xmat[trunk_id].reshape(3, 3)[2, 2])
        min_upright = min(min_upright, upright)
        max_contacts = max(max_contacts, int(data.ncon))
        if t >= ramp_s:
            min_contacts_after_ramp = min(min_contacts_after_ramp, int(data.ncon))

        if not finite or data.qpos[2] < 0.075 or upright < math.cos(math.radians(55.0)):
            break

    passed = (
        finite
        and step == steps - 1
        and min_contacts_after_ramp > 0
        and min_upright > math.cos(math.radians(25.0))
    )
    return {
        "knee_deg": knee_deg,
        "hip_deg": math.degrees(hip),
        "passed": passed,
        "duration": float(data.time),
        "height": float(data.qpos[2]),
        "min_height": min_height,
        "max_tilt_deg": math.degrees(math.acos(np.clip(min_upright, -1.0, 1.0))),
        "min_contacts": min_contacts_after_ramp,
        "max_contacts": max_contacts,
        "drift_x": float(data.qpos[0]),
    }


def main() -> None:
    model = mujoco.MjModel.from_xml_path(XML)
    print("Fixed compound-rocker crouch test")
    print("knee    hip    result  time   end_z  tilt  contacts  drift_x")
    print("-" * 72)
    results = []
    for knee_deg in (0.0, 10.0, 15.0, 20.0, 25.0, 30.0):
        result = run_trial(model, knee_deg)
        results.append(result)
        print(
            f"{result['knee_deg']:4.0f}  {result['hip_deg']:6.2f}  "
            f"{'PASS' if result['passed'] else 'FAIL':>6s}  "
            f"{result['duration']:4.1f}  {result['height']:6.4f}  "
            f"{result['max_tilt_deg']:5.1f}  "
            f"{result['min_contacts']:2d}..{result['max_contacts']:<2d}  "
            f"{result['drift_x']:+.4f}"
        )
    passed = all(r["passed"] for r in results)
    print("-" * 72)
    print("ALL ROCKER TESTS PASSED:", passed)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
