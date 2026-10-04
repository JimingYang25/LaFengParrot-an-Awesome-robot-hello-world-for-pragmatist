import argparse
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.running_mean_std import RunningMeanStd
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize

from rl.lafengparrot_walk_env import LaFengParrotWalkEnv


ROOT = Path(__file__).resolve().parents[1]
STAND_DIR = ROOT / "rl" / "runs" / "stand_ppo_v2"
RUN_DIR = ROOT / "rl" / "runs" / "walk_ppo_v1"
CHECKPOINT_DIR = RUN_DIR / "checkpoints"


def make_env(rank, seed, target_speed):
    def _init():
        env = LaFengParrotWalkEnv(target_speed=target_speed)
        env.reset(seed=seed + rank)
        return Monitor(env)

    return _init


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=1_000_000)
    parser.add_argument("--envs", type=int, default=16)
    parser.add_argument("--seed", type=int, default=84)
    parser.add_argument("--speed", type=float, default=0.08)
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cuda",
    )
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    vec_env = SubprocVecEnv(
        [
            make_env(rank, args.seed, args.speed)
            for rank in range(args.envs)
        ],
        start_method="forkserver",
    )

    # Retain the standing policy's observation normalization, but learn new
    # walking-reward statistics from scratch.
    env = VecNormalize.load(
        STAND_DIR / "vecnormalize_best.pkl",
        vec_env,
    )
    env.training = True
    env.norm_reward = True
    env.ret_rms = RunningMeanStd(shape=())
    env.returns = np.zeros(env.num_envs)

    checkpoint_callback = CheckpointCallback(
        save_freq=max(100_000 // args.envs, 1),
        save_path=str(CHECKPOINT_DIR),
        name_prefix="walk_ppo",
        save_vecnormalize=True,
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=1e-4,
        n_steps=1024,
        batch_size=2048,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.001,
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

    # Same observation/action dimensions and network architecture: initialize
    # the walking policy with the strongest standing checkpoint.
    stand_model = PPO.load(
        STAND_DIR / "stand_ppo_best.zip",
        device=args.device,
    )
    model.policy.load_state_dict(stand_model.policy.state_dict())
    del stand_model

    model.learn(
        total_timesteps=args.steps,
        callback=checkpoint_callback,
        tb_log_name="walk_v1",
    )

    model.save(RUN_DIR / "walk_ppo_final")
    env.save(RUN_DIR / "vecnormalize.pkl")
    env.close()

    print("\nWalking training complete")
    print("Model:", RUN_DIR / "walk_ppo_final.zip")
    print("Normalization:", RUN_DIR / "vecnormalize.pkl")


if __name__ == "__main__":
    main()
