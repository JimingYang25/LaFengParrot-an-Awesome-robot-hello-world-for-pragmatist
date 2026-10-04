"""Regression tests for ground-contact and cross-foot classification."""

from __future__ import annotations

import unittest

import mujoco
import numpy as np

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


# Captured from a deterministic replay of the published h008 checkpoint. The
# base is lifted in the test so the only contact is left sole versus right sole.
CROSS_FOOT_QPOS = np.array(
    [
        0.036065096659069776,
        0.008688093259044195,
        0.250000000000000000,
        0.9913975644982758,
        -0.04396083771175109,
        0.030887021016124547,
        0.11934951104766747,
        -0.00575721182069997,
        -0.33556725596438247,
        1.0802626827610646,
        0.0689432506636639,
        -0.04350169241106281,
        0.023081253430896922,
        -0.0002771675325129072,
        -0.00027459959943196716,
        0.000002069690335046749,
        0.0000499887848733655,
    ],
    dtype=np.float64,
)


class GaitContactClassificationTest(unittest.TestCase):
    def setUp(self):
        self.env = LaFengParrotGaitEnv(harness_strength=0.08)

    def tearDown(self):
        self.env.close()

    def test_standing_soles_contact_floor_without_self_collision(self):
        self.env.reset(seed=0)
        self.env.data.qpos[0:3] = [0.0, 0.0, self.env.stand_height]
        self.env.data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]
        self.env.data.qpos[self.env.joint_qpos_addresses] = 0.0
        self.env.data.qvel[:] = 0.0
        mujoco.mj_forward(self.env.model, self.env.data)

        np.testing.assert_array_equal(
            self.env._contacts_now(),
            np.ones(2, dtype=np.float64),
        )
        self.assertEqual(self.env._cross_foot_contact_count(), 0)

    def test_crossed_feet_in_air_are_not_ground_contacts(self):
        self.env.reset(seed=0)
        self.env.data.qpos[:] = CROSS_FOOT_QPOS
        self.env.data.qvel[:] = 0.0
        mujoco.mj_forward(self.env.model, self.env.data)

        self.assertGreater(self.env._cross_foot_contact_count(), 0)
        np.testing.assert_array_equal(
            self.env._contacts_now(),
            np.zeros(2, dtype=np.float64),
        )
        np.testing.assert_array_equal(
            self.env._contact_slip_speeds(),
            np.zeros(2, dtype=np.float64),
        )

    def test_persistent_cross_foot_contact_terminates_episode(self):
        self.env.reset(seed=0)
        self.env._cross_foot_contact_count = lambda: 1
        action = np.zeros(self.env.action_space.shape, dtype=np.float32)

        for expected_steps in (1, 2):
            _, _, terminated, truncated, info = self.env.step(action)
            self.assertFalse(terminated)
            self.assertFalse(truncated)
            self.assertEqual(info["cross_foot_contact_steps"], expected_steps)

        _, _, terminated, _, info = self.env.step(action)
        self.assertTrue(terminated)
        self.assertEqual(info["cross_foot_contact_steps"], 3)
        self.assertEqual(info["episode_cross_foot_contacts"], 3)


if __name__ == "__main__":
    unittest.main()
