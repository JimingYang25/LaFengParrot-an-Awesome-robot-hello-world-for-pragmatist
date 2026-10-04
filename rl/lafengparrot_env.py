from pathlib import Path

import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np


class LaFengParrotStandEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        xml_path = (
            Path(__file__).resolve().parents[1]
            / "robot_description"
            / "mjcf"
            / "lafengparrot.xml"
        )

        self.model = mujoco.MjModel.from_xml_path(str(xml_path))
        self.data = mujoco.MjData(self.model)

        self.frame_skip = 10
        self.max_episode_steps = 1000
        self.elapsed_steps = 0
        # Physical rocker-sole underside is 138 mm below the trunk origin.
        self.stand_height = 0.138

        self.trunk_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY,
            "trunk",
        )

        # Safer training ranges than the complete mechanical ranges.
        training_limits_deg = {
            "hip_roll_L": (-8, 8),
            "hip_roll_R": (-8, 8),
            "hip_pitch_L": (-20, 20),
            "hip_pitch_R": (-20, 20),
            "knee_L": (0, 30),
            "knee_R": (0, 30),

            # Phase 1: keep expressive joints neutral.
            "wing_flap_L": (0, 0),
            "wing_flap_R": (0, 0),
            "neck_yaw": (0, 0),
            "neck_pitch": (0, 0),
        }

        self.ctrl_low = np.zeros(self.model.nu)
        self.ctrl_high = np.zeros(self.model.nu)

        for actuator_id in range(self.model.nu):
            name = mujoco.mj_id2name(
                self.model,
                mujoco.mjtObj.mjOBJ_ACTUATOR,
                actuator_id,
            )
            low_deg, high_deg = training_limits_deg[name]
            model_low, model_high = self.model.actuator_ctrlrange[actuator_id]

            self.ctrl_low[actuator_id] = max(
                np.deg2rad(low_deg), model_low
            )
            self.ctrl_high[actuator_id] = min(
                np.deg2rad(high_deg), model_high
            )

        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.model.nu,),
            dtype=np.float32,
        )

        # height + quaternion + 10 joint positions
        # + 16 velocities + previous 10 actions = 41
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(41,),
            dtype=np.float32,
        )

        self.filtered_action = np.zeros(
            self.model.nu, dtype=np.float64
        )

        self.push_force = np.zeros(3, dtype=np.float64)
        self.push_remaining = 0
        self.next_push_step = 0

    def _get_obs(self):
        return np.concatenate(
            [
                self.data.qpos[2:],       # Ignore global X/Y position.
                self.data.qvel,
                self.filtered_action,
            ]
        ).astype(np.float32)

    def _action_to_ctrl(self, action):
        # Zero action corresponds to the neutral standing position.
        # The knee's negative action maps to zero because it cannot bend
        # in the negative direction.
        return np.where(
            action >= 0.0,
            action * self.ctrl_high,
            (-action) * self.ctrl_low,
        )

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)

        mujoco.mj_resetData(self.model, self.data)
        self.elapsed_steps = 0
        self.filtered_action[:] = 0.0
        self.data.xfrc_applied[:] = 0.0
        self.push_force[:] = 0.0
        self.push_remaining = 0
        self.next_push_step = int(
            self.np_random.integers(100, 251)
        )
        self.data.qpos[0:3] = [0.0, 0.0, self.stand_height]

        # Small randomized initial body tilt.
        roll, pitch = self.np_random.uniform(
            np.deg2rad(-3),
            np.deg2rad(3),
            size=2,
        )

        cr, sr = np.cos(roll / 2), np.sin(roll / 2)
        cp, sp = np.cos(pitch / 2), np.sin(pitch / 2)

        # MuJoCo quaternion order: w, x, y, z.
        self.data.qpos[3:7] = [
            cr * cp,
            sr * cp,
            cr * sp,
            -sr * sp,
        ]

        # Small initial horizontal and angular disturbance.
        self.data.qvel[0:2] = self.np_random.uniform(-0.05, 0.05, 2)
        self.data.qvel[3:5] = self.np_random.uniform(-0.10, 0.10, 2)

        self.data.ctrl[:] = 0.0
        mujoco.mj_forward(self.model, self.data)

        return self._get_obs(), {}

    def step(self, action):
        action = np.asarray(action, dtype=np.float64)
        action = np.clip(action, -1.0, 1.0)

        # Smooth commands to resemble real servo communication.
        previous_filtered_action = self.filtered_action.copy()
        self.filtered_action = (
            0.8 * self.filtered_action + 0.2 * action
        )
        self.data.ctrl[:] = self._action_to_ctrl(
            self.filtered_action
        )
        # Apply a 0.1-second horizontal push every 3–6 seconds.
        self.data.xfrc_applied[:] = 0.0

        if (
            self.push_remaining == 0
            and self.elapsed_steps >= self.next_push_step
        ):
            angle = self.np_random.uniform(0.0, 2.0 * np.pi)
            magnitude = self.np_random.uniform(1.5, 3.0)

            self.push_force[:] = [
                magnitude * np.cos(angle),
                magnitude * np.sin(angle),
                0.0,
            ]
            self.push_remaining = 5
            self.next_push_step = (
                self.elapsed_steps
                + int(self.np_random.integers(150, 301))
            )

        if self.push_remaining > 0:
            self.data.xfrc_applied[
                self.trunk_id, :3
            ] = self.push_force
            self.push_remaining -= 1

        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)

        self.elapsed_steps += 1

        finite = bool(
            np.all(np.isfinite(self.data.qpos))
            and np.all(np.isfinite(self.data.qvel))
        )

        if finite:
            height = float(self.data.qpos[2])
            rotation = self.data.xmat[self.trunk_id].reshape(3, 3)
            upright = float(rotation[2, 2])
        else:
            height = -1.0
            upright = -1.0

        height_error = height - self.stand_height

        action_delta = (
            self.filtered_action - previous_filtered_action
        )

        reward = (
            1.0
            + 1.5 * upright
            - 20.0 * height_error**2
            - 0.02 * np.sum(self.data.qvel[:6] ** 2)
            - 0.002 * np.sum(self.data.qvel[6:] ** 2)
            - 0.05 * np.sum(self.filtered_action**2)
            - 0.02 * np.sum(action_delta**2)
        )

        terminated = bool(
            not finite
            or height < 0.09
            or upright < 0.5
        )
        truncated = self.elapsed_steps >= self.max_episode_steps

        if terminated:
            reward -= 25.0

        info = {
            "height": height,
            "upright": upright,
            "control_dt": self.model.opt.timestep * self.frame_skip,
        }

        return (
            self._get_obs(),
            float(reward),
            terminated,
            truncated,
            info,
        )

    def close(self):
        pass
