"""Visualize a single-leg lift diagnostic.

This is not walking and is not an RL policy. It is a deterministic LEFT-foot
lift with a training-only virtual balance
harness.  The harness applies lateral force plus roll/pitch torque to the trunk;
it applies no forward force.  PPO will learn residual balance while this support
is annealed to zero, so the real robot does not need any additional hardware.
"""
from __future__ import annotations

import math
from pathlib import Path
import time

import mujoco
import mujoco.viewer
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "robot_description" / "mjcf" / "lafengparrot.xml"

CONTROL_NAMES = (
    "hip_roll_L",
    "hip_roll_R",
    "hip_pitch_L",
    "hip_pitch_R",
    "knee_L",
    "knee_R",
)


def pose(roll=0.0, hip_l=0.0, hip_r=0.0, knee_l=0.0, knee_r=0.0):
    return np.deg2rad([roll, roll, hip_l, hip_r, knee_l, knee_r])


# Selected from a deterministic sweep.  The left sole clears the floor by
# about 14 mm, returns to contact, and advances the base by about 5 mm.
SEQUENCE = (
    ("settle", pose(), 0.8),
    ("load right", pose(-1.5), 1.5),
    ("lift left", pose(-1.5, 0.0, -5.0, 40.0, 0.0), 1.5),
    ("swing left", pose(-1.5, 0.0, -5.0, 40.0, 0.0), 1.5),
    ("land left", pose(-1.5, 0.0, -5.0, 0.0, 0.0), 1.5),
    ("hold", pose(-1.5, 0.0, -5.0, 0.0, 0.0), 1.0),
)


def apply_training_harness(model, data, trunk_id, strength=1.0):
    """Apply training-only balance assistance, never forward propulsion."""
    data.xfrc_applied[:] = 0.0
    rotation = data.xmat[trunk_id].reshape(3, 3)
    up = rotation[:, 2]
    upright_error_axis = np.cross(up, np.array([0.0, 0.0, 1.0]))

    force_y = -180.0 * data.qpos[1] - 18.0 * data.qvel[1]
    torque = 5.0 * upright_error_axis - 0.45 * data.qvel[3:6]

    data.xfrc_applied[trunk_id, 1] = strength * np.clip(force_y, -10.0, 10.0)
    data.xfrc_applied[trunk_id, 3:6] = strength * np.clip(
        torque, -1.0, 1.0
    )


def contact_count(data, sole_geom_ids):
    count = 0
    for contact_id in range(data.ncon):
        contact = data.contact[contact_id]
        if contact.geom1 in sole_geom_ids or contact.geom2 in sole_geom_ids:
            count += 1
    return count


def main():
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    trunk_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, "trunk"
    )
    actuator_ids = {
        name: mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_ACTUATOR, name
        )
        for name in CONTROL_NAMES
    }
    left_center_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_GEOM, "shin_L_sole"
    )
    left_sole_ids = {
        geom_id
        for geom_id in range(model.ngeom)
        if (
            (name := mujoco.mj_id2name(
                model, mujoco.mjtObj.mjOBJ_GEOM, geom_id
            ))
            and name.startswith("shin_L_sole")
        )
    }

    control_dt = model.opt.timestep * 10
    print("Single-leg lift diagnostic: training harness ON")
    print("The harness stabilizes balance only; forward force is always zero.")
    print("Close the viewer or press Ctrl+C to stop.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.lookat[:] = [0.0, 0.0, 0.08]
        viewer.cam.distance = 0.48
        viewer.cam.azimuth = 150
        viewer.cam.elevation = -15

        episode = 0
        while viewer.is_running():
            mujoco.mj_resetData(model, data)
            data.qpos[2] = 0.138
            data.ctrl[:] = 0.0
            mujoco.mj_forward(model, data)

            start_x = float(data.qpos[0])
            max_clearance = 0.0
            max_tilt = 0.0
            saw_flight = False
            previous = np.zeros(len(CONTROL_NAMES))

            for phase_name, target, duration in SEQUENCE:
                frames = max(1, round(duration / control_dt))
                phase_start = previous.copy()

                for frame in range(frames):
                    if not viewer.is_running():
                        return
                    frame_start = time.perf_counter()
                    blend = (frame + 1) / frames
                    blend = blend * blend * (3.0 - 2.0 * blend)
                    command = phase_start + blend * (target - phase_start)

                    for index, name in enumerate(CONTROL_NAMES):
                        data.ctrl[actuator_ids[name]] = command[index]

                    for _ in range(10):
                        apply_training_harness(model, data, trunk_id)
                        mujoco.mj_step(model, data)

                    clearance = float(
                        data.geom_xpos[left_center_id, 2] - 0.0015
                    )
                    max_clearance = max(max_clearance, clearance)
                    saw_flight |= (
                        contact_count(data, left_sole_ids) == 0
                        and clearance > 0.002
                    )
                    upright = float(
                        data.xmat[trunk_id].reshape(3, 3)[2, 2]
                    )
                    max_tilt = max(
                        max_tilt,
                        math.degrees(
                            math.acos(np.clip(upright, -1.0, 1.0))
                        ),
                    )

                    viewer.cam.lookat[0] = float(data.qpos[0])
                    viewer.sync()
                    remaining = control_dt - (
                        time.perf_counter() - frame_start
                    )
                    if remaining > 0.0:
                        time.sleep(remaining)

                previous = target
                print(f"phase: {phase_name}", flush=True)

            episode += 1
            final_contacts = contact_count(data, left_sole_ids)
            print(
                f"step={episode} forward={data.qpos[0] - start_x:+.4f} m "
                f"left_clearance={max_clearance * 1000:.1f} mm "
                f"flight={saw_flight} landed={final_contacts > 0} "
                f"max_tilt={max_tilt:.1f} deg",
                flush=True,
            )
            time.sleep(0.5)


if __name__ == "__main__":
    main()
