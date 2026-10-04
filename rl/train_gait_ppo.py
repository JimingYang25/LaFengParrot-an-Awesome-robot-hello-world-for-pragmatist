import argparse
import pickle
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CallbackList,
    CheckpointCallback,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize

from rl.lafengparrot_gait_env import LaFengParrotGaitEnv


STAND_DIR = ROOT / "rl" / "runs" / "stand_ppo_rocker32"
RUN_DIR = ROOT / "rl" / "runs" / "gait_ppo_v3_valid"
CHECKPOINT_DIR = RUN_DIR / "checkpoints"


def make_env(rank, seed, target_speed, harness_strength):
    def _init():
        env = LaFengParrotGaitEnv(
            target_speed=target_speed,
            harness_strength=harness_strength,
        )
        env.reset(seed=seed + rank)
        return Monitor(env)

    return _init


def copy_standing_normalization(target_env):
    with open(STAND_DIR / "vecnormalize.pkl", "rb") as handle:
        old_wrapper = pickle.load(handle)

    target_env.obs_rms.mean[:41] = old_wrapper.obs_rms.mean
    target_env.obs_rms.var[:41] = old_wrapper.obs_rms.var
    target_env.obs_rms.mean[41:] = 0.0
    target_env.obs_rms.var[41:] = 1.0
    target_env.obs_rms.count = old_wrapper.obs_rms.count


def copy_standing_policy(target_model, device):
    old_model = PPO.load(
        STAND_DIR / "stand_ppo_final.zip",
        device=device,
    )
    old_state = old_model.policy.state_dict()
    new_state = target_model.policy.state_dict()

    for name, old_tensor in old_state.items():
        if name not in new_state:
            continue
        new_tensor = new_state[name]
        if new_tensor.shape == old_tensor.shape:
            new_state[name] = old_tensor
        elif (
            new_tensor.ndim == 2
            and old_tensor.ndim == 2
            and new_tensor.shape[0] == old_tensor.shape[0]
            and new_tensor.shape[1] > old_tensor.shape[1]
        ):
            new_tensor[:, : old_tensor.shape[1]] = old_tensor
            new_tensor[:, old_tensor.shape[1] :] = 0.0
            new_state[name] = new_tensor

    target_model.policy.load_state_dict(new_state)
    del old_model


class HarnessAnnealingCallback(BaseCallback):
    """Fade the training-only balance harness while PPO learns residuals."""

    def __init__(self, start, end, decay_fraction, verbose=0):
        super().__init__(verbose=verbose)
        self.start = float(start)
        self.end = float(end)
        self.decay_fraction = float(decay_fraction)
        self.last_strength = None
        self.stage_start_timestep = 0
        self.stage_timesteps = 1

    def _set_strength(self):
        denominator = max(1.0, self.decay_fraction * self.stage_timesteps)
        progress = np.clip(
            (self.num_timesteps - self.stage_start_timestep) / denominator,
            0.0,
            1.0,
        )
        strength = self.start + progress * (self.end - self.start)
        if self.last_strength is None or abs(strength - self.last_strength) >= 0.001:
            self.training_env.env_method("set_harness_strength", strength)
            self.last_strength = strength
        self.logger.record("curriculum/harness_strength", strength)

    def _on_training_start(self):
        self.stage_start_timestep = self.num_timesteps
        self.stage_timesteps = max(
            1,
            self.model._total_timesteps - self.stage_start_timestep,
        )
        self._set_strength()

    def _on_step(self):
        self._set_strength()
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=3_000_000)
    parser.add_argument("--envs", type=int, default=16)
    parser.add_argument("--seed", type=int, default=126)
    parser.add_argument("--speed", type=float, default=0.025)
    parser.add_argument("--start-harness", type=float, default=1.0)
    parser.add_argument("--end-harness", type=float, default=0.0)
    parser.add_argument("--decay-fraction", type=float, default=0.80)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue gait_ppo_v3_valid from its final model and normalization.",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cuda",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-rollout tables during long unattended stages.",
    )
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    vec_env = SubprocVecEnv(
        [
            make_env(rank, args.seed, args.speed, args.start_harness)
            for rank in range(args.envs)
        ],
        start_method="forkserver",
    )
    if args.resume:
        env = VecNormalize.load(RUN_DIR / "vecnormalize.pkl", vec_env)
        env.training = True
        env.norm_reward = True
    else:
        env = VecNormalize(
            vec_env,
            norm_obs=True,
            norm_reward=True,
            clip_obs=10.0,
            clip_reward=10.0,
            gamma=0.99,
        )
        copy_standing_normalization(env)

    checkpoint_callback = CheckpointCallback(
        save_freq=max(100_000 // args.envs, 1),
        save_path=str(CHECKPOINT_DIR),
        name_prefix="gait_ppo",
        save_vecnormalize=True,
    )
    harness_callback = HarnessAnnealingCallback(
        start=args.start_harness,
        end=args.end_harness,
        decay_fraction=args.decay_fraction,
    )

    if args.resume:
        model = PPO.load(
            RUN_DIR / "gait_ppo_final.zip",
            env=env,
            device=args.device,
            tensorboard_log=str(RUN_DIR / "tensorboard"),
        )
    else:
        model = PPO(
            policy="MlpPolicy",
            env=env,
            learning_rate=2e-4,
            n_steps=1024,
            batch_size=2048,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.002,
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs={
                "log_std_init": -1.5,
                "net_arch": {
                    "pi": [256, 256],
                    "vf": [256, 256],
                },
            },
            tensorboard_log=str(RUN_DIR / "tensorboard"),
            device=args.device,
            seed=args.seed,
            verbose=1,
        )
        copy_standing_policy(model, args.device)

    if args.quiet:
        model.verbose = 0

    model.learn(
        total_timesteps=args.steps,
        callback=CallbackList([checkpoint_callback, harness_callback]),
        tb_log_name="gait_v3_valid",
        reset_num_timesteps=not args.resume,
    )

    model.save(RUN_DIR / "gait_ppo_final")
    env.save(RUN_DIR / "vecnormalize.pkl")
    env.close()

    print("\nGait training complete")
    print("Model:", RUN_DIR / "gait_ppo_final.zip")
    print("Normalization:", RUN_DIR / "vecnormalize.pkl")


if __name__ == "__main__":
    main()
