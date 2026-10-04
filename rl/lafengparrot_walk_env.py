import numpy as np

from rl.lafengparrot_env import LaFengParrotStandEnv


class LaFengParrotWalkEnv(LaFengParrotStandEnv):
    """Phase-2 task: walk forward while retaining the learned balance skill."""

    def __init__(self, target_speed=0.08):
        super().__init__()
        self.target_speed = float(target_speed)
        self.start_x = 0.0

    def reset(self, *, seed=None, options=None):
        obs, info = super().reset(seed=seed, options=options)

        # Walking curriculum V1 has no external pushes. First learn a gait;
        # robustness disturbances return in a later curriculum stage.
        self.push_remaining = 0
        self.next_push_step = self.max_episode_steps + 1
        self.data.xfrc_applied[:] = 0.0
        self.start_x = float(self.data.qpos[0])

        info.update(
            {
                "target_speed": self.target_speed,
                "forward_speed": float(self.data.qvel[0]),
                "distance": 0.0,
            }
        )
        return obs, info

    def step(self, action):
        obs, _, terminated, truncated, info = super().step(action)

        forward_speed = float(self.data.qvel[0])
        lateral_speed = float(self.data.qvel[1])
        yaw_rate = float(self.data.qvel[5])
        height = float(info["height"])
        upright = float(info["upright"])
        distance = float(self.data.qpos[0] - self.start_x)

        speed_scale = 0.05
        speed_reward = np.exp(
            -((forward_speed - self.target_speed) / speed_scale) ** 2
        )
        upright_reward = np.clip((upright - 0.5) / 0.5, 0.0, 1.0)
        height_reward = np.exp(
            -200.0 * (height - self.stand_height) ** 2
        )

        reward = (
            0.30
            + 1.50 * speed_reward
            + 0.50 * upright_reward
            + 0.20 * height_reward
            - 0.20 * lateral_speed**2
            - 0.10 * yaw_rate**2
            - 0.003 * np.sum(self.data.qvel[6:] ** 2)
            - 0.02 * np.sum(self.filtered_action**2)
            - 1.00 * max(0.0, -forward_speed)
        )

        # Keep the first walking curriculum in a narrow forward corridor.
        if abs(float(self.data.qpos[1])) > 0.25:
            terminated = True

        if terminated:
            reward -= 25.0

        info.update(
            {
                "target_speed": self.target_speed,
                "forward_speed": forward_speed,
                "distance": distance,
                "speed_reward": float(speed_reward),
            }
        )

        return obs, float(reward), bool(terminated), bool(truncated), info
