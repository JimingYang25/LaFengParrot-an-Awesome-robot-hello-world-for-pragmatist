"""Walking-V2 environment for the LaFengParrot.

The task is intentionally event based. A policy only receives a completed
cycle reward after this ordered sequence:

    left flight -> left touchdown -> right flight -> right touchdown

The final touchdown must also leave the trunk farther forward. This prevents
the one-leg balancing solution that can score well in a velocity-only task.
"""
from __future__ import annotations

import math

from gymnasium import spaces
import mujoco
import numpy as np

from rl.lafengparrot_env import LaFengParrotStandEnv


class LaFengParrotGaitEnv(LaFengParrotStandEnv):
    """Residual-policy gait task with an annealable training harness."""

    CONTROL_NAMES = (
        "hip_roll_L",
        "hip_roll_R",
        "hip_pitch_L",
        "hip_pitch_R",
        "knee_L",
        "knee_R",
    )

    # Validated forward-step reference.  Pitch stays frozen while both feet
    # are down; each knee lifts before its hip swings, then extends only after
    # the foot is ahead.  Values are joint targets in degrees.
    REFERENCE_KNOTS = (
        (0.000, (0.926053, 0.926053, 9.638486, -20.676886, 0.0, 0.0)),
        (0.100, (-0.926053, -0.926053, 9.638486, -20.676886, 0.0, 0.0)),
        (0.180, (-0.926053, -0.926053, 9.638486, -20.676886, 56.961069, 0.0)),
        (0.340, (-0.926053, -0.926053, -20.676886, 9.638486, 56.961069, 0.0)),
        (0.413692, (-0.926053, -0.926053, -20.676886, 9.638486, 0.0, 0.0)),
        (0.580, (0.926053, 0.926053, -20.676886, 9.638486, 0.0, 0.0)),
        (0.680, (0.926053, 0.926053, -20.676886, 9.638486, 0.0, 56.961069)),
        (0.840, (0.926053, 0.926053, 9.638486, -20.676886, 0.0, 56.961069)),
        (0.930151, (0.926053, 0.926053, 9.638486, -20.676886, 0.0, 0.0)),
        (1.000, (0.926053, 0.926053, 9.638486, -20.676886, 0.0, 0.0)),
    )

    def __init__(
        self,
        target_speed=0.025,
        gait_frequency=0.244990793,
        harness_strength=1.0,
        reset_noise_scale=0.25,
    ):
        self.gait_phase = 0.0
        self.target_speed = float(target_speed)
        self.gait_frequency = float(gait_frequency)
        self.harness_strength = float(harness_strength)
        self.reset_noise_scale = float(reset_noise_scale)

        # Fields used by _get_obs; super().reset dispatches to that method.
        self.gait_event_state = 0
        self.desired_contacts = np.ones(2, dtype=np.float64)
        self.foot_contacts = np.ones(2, dtype=np.float64)
        self.foot_positions = np.zeros(4, dtype=np.float64)
        self.foot_velocities = np.zeros(4, dtype=np.float64)
        self.foot_world_x = np.zeros(2, dtype=np.float64)
        self.contact_slip_speed = np.zeros(2, dtype=np.float64)
        self.cycle_slip_distance = np.zeros(2, dtype=np.float64)

        super().__init__()

        self.control_dt = self.model.opt.timestep * self.frame_skip
        self.actuator_ids = {
            name: mujoco.mj_name2id(
                self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name
            )
            for name in self.CONTROL_NAMES
        }
        self.joint_qpos_addresses = np.array(
            [
                self.model.jnt_qposadr[
                    self.model.actuator_trnid[self.actuator_ids[name], 0]
                ]
                for name in self.CONTROL_NAMES
            ],
            dtype=np.int32,
        )
        self.joint_qvel_addresses = np.array(
            [
                self.model.jnt_dofadr[
                    self.model.actuator_trnid[self.actuator_ids[name], 0]
                ]
                for name in self.CONTROL_NAMES
            ],
            dtype=np.int32,
        )

        self.sole_geom_ids = {}
        self.sole_center_ids = {}
        self.floor_geom_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_GEOM,
            "floor",
        )
        if self.floor_geom_id < 0:
            raise ValueError("MJCF must define a geom named 'floor'")
        self._floor_geom_ids = {self.floor_geom_id}
        for index, side in enumerate(("L", "R")):
            prefix = f"shin_{side}_sole"
            self.sole_geom_ids[index] = {
                geom_id
                for geom_id in range(self.model.ngeom)
                if (
                    (name := mujoco.mj_id2name(
                        self.model, mujoco.mjtObj.mjOBJ_GEOM, geom_id
                    ))
                    and name.startswith(prefix)
                )
            }
            self.sole_center_ids[index] = mujoco.mj_name2id(
                self.model, mujoco.mjtObj.mjOBJ_GEOM, prefix
            )

        # The policy is a bounded residual around the gait reference.
        self.residual_scale = np.deg2rad(
            [8.0, 8.0, 18.0, 18.0, 20.0, 20.0, 0.0, 0.0, 0.0, 0.0]
        )

        # 41 standing terms + clock(2) + foot x/z(4) + foot vx/vz(4)
        # + actual contacts(2) + contact-point slip speed(2) + event one-hot(4)
        # + harness strength(1) = 60.
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(60,),
            dtype=np.float32,
        )

        self.start_x = 0.0
        self.cycle_start_x = 0.0
        self.completed_cycles = 0
        self.successful_cycles = 0
        self.steps_since_event = 0
        # One missed phase may recover on the next reference cycle. A static
        # one-leg pose still terminates because it cannot complete the event.
        self.event_timeout_steps = max(1, round(4.0 / self.control_dt))
        self._off_counts = np.zeros(2, dtype=np.int32)
        self._on_counts = np.zeros(2, dtype=np.int32)
        self.flight_steps = 0
        self.flight_clearance = 0.0
        self.touchdown_valid = np.zeros(2, dtype=bool)
        self.touchdown_lead = np.zeros(2, dtype=np.float64)
        self.max_cycle_slip = 0.0
        self.last_cycle_slip_distance = np.zeros(2, dtype=np.float64)
        self.last_cycle_valid = False
        self.invalid_touchdown = False
        self.invalid_touchdown_steps = 0
        self.cross_foot_contact_count = 0
        self.cross_foot_contact_steps = 0
        self.episode_cross_foot_contacts = 0
        self.foot_lateral_separation = float("inf")
        self.minimum_foot_lateral_separation = float("inf")
        self._geom_velocity = np.zeros(6, dtype=np.float64)

    def set_harness_strength(self, strength):
        """Set curriculum assistance; 0.0 is the deployable task."""
        self.harness_strength = float(np.clip(strength, 0.0, 1.0))

    @staticmethod
    def _smoothstep(value):
        value = float(np.clip(value, 0.0, 1.0))
        return value * value * (3.0 - 2.0 * value)

    def _reference_six(self, phase=None):
        phase = self.gait_phase if phase is None else float(phase) % 1.0
        for (time_a, pose_a), (time_b, pose_b) in zip(
            self.REFERENCE_KNOTS[:-1], self.REFERENCE_KNOTS[1:]
        ):
            if time_a <= phase <= time_b:
                blend = self._smoothstep((phase - time_a) / (time_b - time_a))
                pose_a = np.asarray(pose_a, dtype=np.float64)
                pose_b = np.asarray(pose_b, dtype=np.float64)
                return np.deg2rad(pose_a + blend * (pose_b - pose_a))
        return np.deg2rad(self.REFERENCE_KNOTS[-1][1])

    def _reference_ctrl(self):
        result = np.zeros(self.model.nu, dtype=np.float64)
        reference = self._reference_six()
        for index, name in enumerate(self.CONTROL_NAMES):
            result[self.actuator_ids[name]] = reference[index]
        return result

    @staticmethod
    def _contact_between(contact, geom_ids_a, geom_ids_b):
        geom1 = int(contact.geom1)
        geom2 = int(contact.geom2)
        return bool(
            (geom1 in geom_ids_a and geom2 in geom_ids_b)
            or (geom2 in geom_ids_a and geom1 in geom_ids_b)
        )

    def _contacts_now(self):
        """Return sole-versus-floor contacts only.

        A sole touching the other foot is a self-collision, not a ground
        contact.  Keeping these signals separate prevents a crossed-foot pose
        from satisfying the gait event detector.
        """
        result = np.zeros(2, dtype=np.float64)
        for contact_id in range(self.data.ncon):
            contact = self.data.contact[contact_id]
            for side in (0, 1):
                if self._contact_between(
                    contact,
                    self.sole_geom_ids[side],
                    self._floor_geom_ids,
                ):
                    result[side] = 1.0
        return result

    def _cross_foot_contact_count(self):
        """Count active contacts between left and right sole geometries."""
        return sum(
            self._contact_between(
                self.data.contact[contact_id],
                self.sole_geom_ids[0],
                self.sole_geom_ids[1],
            )
            for contact_id in range(self.data.ncon)
        )

    def _foot_lateral_center_separation(self):
        left_y = self.data.geom_xpos[self.sole_center_ids[0], 1]
        right_y = self.data.geom_xpos[self.sole_center_ids[1], 1]
        return abs(float(left_y - right_y))

    def _contact_slip_speeds(self):
        """Return each sole's maximum ground-contact tangential speed.

        Measuring the sole geom centre is wrong for a rocker foot: its centre
        legitimately moves while the contact point rolls.  The velocity here
        is evaluated at MuJoCo's actual contact position, so rolling without
        skid is close to zero and sliding is penalized.
        """
        result = np.zeros(2, dtype=np.float64)
        for contact_id in range(self.data.ncon):
            contact = self.data.contact[contact_id]
            for side in (0, 1):
                sole_ids = self.sole_geom_ids[side]
                if (
                    contact.geom1 in sole_ids
                    and contact.geom2 == self.floor_geom_id
                ):
                    geom_id = int(contact.geom1)
                elif (
                    contact.geom2 in sole_ids
                    and contact.geom1 == self.floor_geom_id
                ):
                    geom_id = int(contact.geom2)
                else:
                    continue
                mujoco.mj_objectVelocity(
                    self.model,
                    self.data,
                    mujoco.mjtObj.mjOBJ_GEOM,
                    geom_id,
                    self._geom_velocity,
                    0,
                )
                angular = self._geom_velocity[:3]
                linear = self._geom_velocity[3:]
                radius = contact.pos - self.data.geom_xpos[geom_id]
                point_velocity = linear + np.cross(angular, radius)
                tangential_speed = float(np.linalg.norm(point_velocity[:2]))
                result[side] = max(result[side], tangential_speed)
        return result

    def _desired_contacts(self):
        phase = self.gait_phase
        if 0.20 <= phase < 0.47:
            return np.array([0.0, 1.0])
        if 0.71 <= phase < 0.97:
            return np.array([1.0, 0.0])
        return np.ones(2, dtype=np.float64)

    def _update_foot_kinematics(self):
        trunk_x = float(self.data.xpos[self.trunk_id, 0])
        positions = np.empty(4, dtype=np.float64)
        for side in (0, 1):
            world = self.data.geom_xpos[self.sole_center_ids[side]]
            self.foot_world_x[side] = world[0]
            positions[2 * side] = world[0] - trunk_x
            positions[2 * side + 1] = world[2]
        self.foot_velocities = (
            positions - self.foot_positions
        ) / self.control_dt
        self.foot_positions = positions

    def _get_obs(self):
        base = super()._get_obs()
        clock = np.array(
            [
                math.sin(2.0 * math.pi * self.gait_phase),
                math.cos(2.0 * math.pi * self.gait_phase),
            ],
            dtype=np.float64,
        )
        event = np.zeros(4, dtype=np.float64)
        event[int(np.clip(self.gait_event_state, 0, 3))] = 1.0
        return np.concatenate(
            [
                base,
                clock,
                self.foot_positions,
                self.foot_velocities,
                self.foot_contacts,
                self.contact_slip_speed,
                event,
                [self.harness_strength],
            ]
        ).astype(np.float32)

    def _apply_training_harness(self):
        self.data.xfrc_applied[:] = 0.0
        if self.harness_strength <= 0.0:
            return

        rotation = self.data.xmat[self.trunk_id].reshape(3, 3)
        upright_error_axis = np.cross(
            rotation[:, 2], np.array([0.0, 0.0, 1.0])
        )
        force_y = -180.0 * self.data.qpos[1] - 18.0 * self.data.qvel[1]
        torque = 5.0 * upright_error_axis - 0.45 * self.data.qvel[3:6]

        # There is deliberately no X force: the harness cannot propel forward.
        self.data.xfrc_applied[self.trunk_id, 1] = (
            self.harness_strength * np.clip(force_y, -10.0, 10.0)
        )
        self.data.xfrc_applied[self.trunk_id, 3:6] = (
            self.harness_strength * np.clip(torque, -1.0, 1.0)
        )

    def reset(self, *, seed=None, options=None):
        self.gait_phase = 0.0
        self.gait_event_state = 0
        self.completed_cycles = 0
        self.successful_cycles = 0
        self.steps_since_event = 0
        self._off_counts[:] = 0
        self._on_counts[:] = 0
        self.flight_steps = 0
        self.flight_clearance = 0.0
        self.touchdown_valid[:] = False
        self.touchdown_lead[:] = 0.0
        self.max_cycle_slip = 0.0
        self.cycle_slip_distance[:] = 0.0
        self.last_cycle_slip_distance[:] = 0.0
        self.last_cycle_valid = False
        self.invalid_touchdown = False
        self.invalid_touchdown_steps = 0
        self.cross_foot_contact_count = 0
        self.cross_foot_contact_steps = 0
        self.episode_cross_foot_contacts = 0
        self.foot_lateral_separation = float("inf")
        self.minimum_foot_lateral_separation = float("inf")

        super().reset(seed=seed, options=options)

        # Start curriculum training with mild disturbances. Strong pushes and
        # full reset randomization belong to the later robustness stage.
        self.data.qpos[4:7] *= self.reset_noise_scale
        self.data.qpos[3:7] /= np.linalg.norm(self.data.qpos[3:7])
        self.data.qvel[:6] *= self.reset_noise_scale

        # Enter a repeatable double-support "walk ready" pose before the
        # first lift.  Starting at phase 0.15 from neutral created an abrupt
        # position-servo transient and unnecessary first-cycle skid.
        self.data.qpos[self.joint_qpos_addresses] = self._reference_six(0.0)
        self.data.qvel[self.joint_qvel_addresses] = 0.0

        # Walking curriculum starts without random impacts. They are added
        # only after unassisted alternating gait passes evaluation.
        self.push_remaining = 0
        self.next_push_step = self.max_episode_steps + 1
        self.data.xfrc_applied[:] = 0.0
        self.data.ctrl[:] = self._reference_ctrl()
        mujoco.mj_forward(self.model, self.data)

        self.start_x = float(self.data.qpos[0])
        self.cycle_start_x = self.start_x
        self.foot_positions[:] = 0.0
        self._update_foot_kinematics()
        self.foot_velocities[:] = 0.0
        self.contact_slip_speed[:] = 0.0
        self.foot_contacts = self._contacts_now()
        self.cross_foot_contact_count = self._cross_foot_contact_count()
        self.foot_lateral_separation = self._foot_lateral_center_separation()
        self.minimum_foot_lateral_separation = self.foot_lateral_separation
        self.desired_contacts = self._desired_contacts()

        info = {
            "target_speed": self.target_speed,
            "forward_speed": float(self.data.qvel[0]),
            "distance": 0.0,
            "gait_phase": self.gait_phase,
            "gait_event": self.gait_event_state,
            "completed_cycles": 0,
            "successful_cycles": 0,
            "harness_strength": self.harness_strength,
        }
        return self._get_obs(), info

    def _debounced_events(self):
        on = self.foot_contacts > 0.5
        self._on_counts = np.where(on, self._on_counts + 1, 0)
        self._off_counts = np.where(~on, self._off_counts + 1, 0)

        event_bonus = 0.0
        cycle_progress = 0.0
        phase = self.gait_phase
        clearance = self.foot_positions[[1, 3]] - 0.0015

        if self.gait_event_state == 0:
            if (
                self._off_counts[0] >= 3
                and clearance[0] >= 0.003
                and 0.18 <= phase < 0.50
            ):
                self.gait_event_state = 1
                self.steps_since_event = 0
                self.flight_steps = int(self._off_counts[0])
                self.flight_clearance = float(clearance[0])
                event_bonus = 1.0
        elif self.gait_event_state == 1:
            if not on[0]:
                if self._off_counts[0] >= 2:
                    self.invalid_touchdown_steps = 0
                    self.invalid_touchdown = False
                self.flight_steps += 1
                self.flight_clearance = max(
                    self.flight_clearance, float(clearance[0])
                )
            elif self._on_counts[0] >= 2:
                if self.invalid_touchdown_steps > 0:
                    self.invalid_touchdown_steps += 1
                    self.invalid_touchdown = self.invalid_touchdown_steps >= 10
                    return -4.0, cycle_progress
                if self.flight_steps < 5 or self.flight_clearance < 0.006:
                    self.flight_steps = 0
                    self.flight_clearance = 0.0
                    return -1.0, cycle_progress
                lead = float(self.foot_world_x[0] - self.foot_world_x[1])
                self.touchdown_lead[0] = lead
                if lead < 0.003:
                    self.invalid_touchdown_steps = 1
                    return -8.0, cycle_progress
                self.touchdown_valid[0] = True
                self.invalid_touchdown_steps = 0
                self.gait_event_state = 2
                self.steps_since_event = 0
                self.flight_steps = 0
                self.flight_clearance = 0.0
                event_bonus = 1.0 + 80.0 * np.clip(lead, -0.03, 0.03)
        elif self.gait_event_state == 2:
            if (
                self._off_counts[1] >= 3
                and clearance[1] >= 0.003
                and 0.68 <= phase < 0.99
            ):
                self.gait_event_state = 3
                self.steps_since_event = 0
                self.flight_steps = int(self._off_counts[1])
                self.flight_clearance = float(clearance[1])
                event_bonus = 1.0
        elif not on[1]:
            if self._off_counts[1] >= 2:
                self.invalid_touchdown_steps = 0
                self.invalid_touchdown = False
            self.flight_steps += 1
            self.flight_clearance = max(
                self.flight_clearance, float(clearance[1])
            )
        elif self._on_counts[1] >= 2:
            if self.invalid_touchdown_steps > 0:
                self.invalid_touchdown_steps += 1
                self.invalid_touchdown = self.invalid_touchdown_steps >= 10
                return -4.0, cycle_progress
            if self.flight_steps < 5 or self.flight_clearance < 0.006:
                self.flight_steps = 0
                self.flight_clearance = 0.0
                return -1.0, cycle_progress
            lead = float(self.foot_world_x[1] - self.foot_world_x[0])
            self.touchdown_lead[1] = lead
            if lead < 0.003:
                self.invalid_touchdown_steps = 1
                return -8.0, cycle_progress
            self.touchdown_valid[1] = True
            self.invalid_touchdown_steps = 0
            cycle_progress = float(self.data.qpos[0] - self.cycle_start_x)
            self.completed_cycles += 1
            valid_cycle = bool(
                np.all(self.touchdown_valid)
                and cycle_progress >= 0.005
                and self.max_cycle_slip <= 0.008
            )
            self.last_cycle_slip_distance = self.cycle_slip_distance.copy()
            self.last_cycle_valid = valid_cycle
            if valid_cycle:
                self.successful_cycles += 1
            self.cycle_start_x = float(self.data.qpos[0])
            self.gait_event_state = 0
            self.steps_since_event = 0
            self.flight_steps = 0
            self.flight_clearance = 0.0
            event_bonus = (
                (12.0 if valid_cycle else -12.0)
                + 80.0 * np.clip(lead, -0.03, 0.03)
                + 150.0 * np.clip(cycle_progress, -0.04, 0.06)
            )
            self.touchdown_valid[:] = False
            self.max_cycle_slip = 0.0
            self.cycle_slip_distance[:] = 0.0

        return float(event_bonus), cycle_progress

    def step(self, action):
        action = np.clip(np.asarray(action, dtype=np.float64), -1.0, 1.0)
        previous_filtered_action = self.filtered_action.copy()
        self.filtered_action = 0.8 * self.filtered_action + 0.2 * action

        reference_ctrl = self._reference_ctrl()
        command = reference_ctrl + self.filtered_action * self.residual_scale
        self.data.ctrl[:] = np.clip(
            command,
            self.model.actuator_ctrlrange[:, 0],
            self.model.actuator_ctrlrange[:, 1],
        )

        for _ in range(self.frame_skip):
            self._apply_training_harness()
            mujoco.mj_step(self.model, self.data)

        self.elapsed_steps += 1
        self.steps_since_event += 1
        self._update_foot_kinematics()
        self.foot_contacts = self._contacts_now()
        self.desired_contacts = self._desired_contacts()
        self.contact_slip_speed = self._contact_slip_speeds()
        self.cross_foot_contact_count = self._cross_foot_contact_count()
        self.episode_cross_foot_contacts += self.cross_foot_contact_count
        if self.cross_foot_contact_count:
            self.cross_foot_contact_steps += 1
        else:
            self.cross_foot_contact_steps = 0
        self.foot_lateral_separation = self._foot_lateral_center_separation()
        self.minimum_foot_lateral_separation = min(
            self.minimum_foot_lateral_separation,
            self.foot_lateral_separation,
        )
        stance_mask = self.desired_contacts * self.foot_contacts
        self.cycle_slip_distance += (
            self.contact_slip_speed * stance_mask * self.control_dt
        )
        self.max_cycle_slip = max(
            self.max_cycle_slip,
            float(np.max(self.cycle_slip_distance)),
        )

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

        event_bonus, cycle_progress = self._debounced_events()
        contact_matches = 1.0 - np.abs(
            self.foot_contacts - self.desired_contacts
        )
        contact_score = float(np.mean(contact_matches))

        reference_six = self._reference_six()
        current_six = self.data.qpos[self.joint_qpos_addresses]
        pose_error = float(np.mean(((current_six - reference_six) / 0.35) ** 2))
        pose_reward = math.exp(-pose_error)

        swing_side = None
        if self.desired_contacts[0] == 0.0:
            swing_side = 0
        elif self.desired_contacts[1] == 0.0:
            swing_side = 1
        if swing_side is None:
            clearance_reward = 0.0
            swing_lead_reward = 0.0
        else:
            clearance = self.foot_positions[2 * swing_side + 1] - 0.0015
            clearance_reward = math.exp(-((clearance - 0.012) / 0.010) ** 2)
            stance_side = 1 - swing_side
            swing_lead = float(
                self.foot_world_x[swing_side] - self.foot_world_x[stance_side]
            )
            swing_lead_reward = math.exp(
                -((swing_lead - 0.020) / 0.018) ** 2
            )

        slip_penalty = float(
            np.sum(
                stance_mask
                * np.clip(self.contact_slip_speed / 0.020, 0.0, 8.0)
            ) / max(1.0, np.sum(stance_mask))
        )
        accumulated_slip_penalty = float(
            np.mean(np.clip(self.cycle_slip_distance / 0.008, 0.0, 4.0))
        )
        # The nominal sole-centre spacing is 54 mm and the two soles occupy
        # 44 mm laterally.  Begin discouraging leg crossing before contact,
        # while retaining a small margin for collision-shape rotation.
        separation_penalty = float(
            np.clip(
                (0.048 - self.foot_lateral_separation) / 0.010,
                0.0,
                2.0,
            )
        )

        forward_speed = float(self.data.qvel[0])
        lateral_speed = float(self.data.qvel[1])
        yaw_rate = float(self.data.qvel[5])
        action_delta = self.filtered_action - previous_filtered_action

        reward = (
            0.05
            + 0.35 * max(upright, 0.0)
            + 0.25 * pose_reward
            + 0.45 * contact_score
            + 0.25 * clearance_reward
            + 0.40 * swing_lead_reward
            + 0.15 * np.clip(forward_speed / self.target_speed, -1.0, 1.0)
            + event_bonus
            - 0.20 * (1.0 - contact_score)
            - 2.00 * slip_penalty
            - 0.80 * accumulated_slip_penalty
            - 0.75 * separation_penalty
            - 4.00 * min(self.cross_foot_contact_count, 2)
            - 0.15 * lateral_speed**2
            - 0.08 * yaw_rate**2
            - 0.008 * np.sum(self.filtered_action**2)
            - 0.015 * np.sum(action_delta**2)
        )

        terminated = bool(
            not finite
            or height < 0.085
            or upright < 0.45
            or abs(float(self.data.qpos[1])) > 0.20
            or self.steps_since_event > self.event_timeout_steps
            or self.invalid_touchdown
            or self.cross_foot_contact_steps >= 3
        )
        truncated = self.elapsed_steps >= self.max_episode_steps
        if terminated:
            reward -= 25.0

        distance = float(self.data.qpos[0] - self.start_x)
        info = {
            "height": height,
            "upright": upright,
            "target_speed": self.target_speed,
            "forward_speed": forward_speed,
            "distance": distance,
            "gait_phase": self.gait_phase,
            "gait_event": self.gait_event_state,
            "event_bonus": event_bonus,
            "cycle_progress": cycle_progress,
            "completed_cycles": self.completed_cycles,
            "successful_cycles": self.successful_cycles,
            "left_contact": bool(self.foot_contacts[0]),
            "right_contact": bool(self.foot_contacts[1]),
            "left_contact_slip_speed": float(self.contact_slip_speed[0]),
            "right_contact_slip_speed": float(self.contact_slip_speed[1]),
            "left_cycle_slip_distance": float(self.cycle_slip_distance[0]),
            "right_cycle_slip_distance": float(self.cycle_slip_distance[1]),
            "left_touchdown_lead": float(self.touchdown_lead[0]),
            "right_touchdown_lead": float(self.touchdown_lead[1]),
            "max_cycle_slip": float(self.max_cycle_slip),
            "last_left_cycle_slip": float(self.last_cycle_slip_distance[0]),
            "last_right_cycle_slip": float(self.last_cycle_slip_distance[1]),
            "last_cycle_valid": bool(self.last_cycle_valid),
            "contact_score": contact_score,
            "harness_strength": self.harness_strength,
            "control_dt": self.control_dt,
            "event_timeout": self.steps_since_event > self.event_timeout_steps,
            "invalid_touchdown": self.invalid_touchdown,
            "invalid_touchdown_steps": self.invalid_touchdown_steps,
            "cross_foot_contact_count": self.cross_foot_contact_count,
            "cross_foot_contact_steps": self.cross_foot_contact_steps,
            "episode_cross_foot_contacts": self.episode_cross_foot_contacts,
            "foot_lateral_separation": self.foot_lateral_separation,
            "minimum_foot_lateral_separation": (
                self.minimum_foot_lateral_separation
            ),
        }

        self.gait_phase = (
            self.gait_phase + self.gait_frequency * self.control_dt
        ) % 1.0

        return (
            self._get_obs(),
            float(reward),
            terminated,
            truncated,
            info,
        )
