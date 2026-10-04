import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize

from rl.lafengparrot_env import LaFengParrotStandEnv


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "rl" / "runs" / "stand_ppo_rocker32"
CHECKPOINT_DIR = RUN_DIR / "checkpoints"


def make_env(rank, seed):
    def _init():
        env = LaFengParrotStandEnv()
        env.reset(seed=seed + rank)
        return Monitor(env)

    return _init


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=100_000)
    parser.add_argument("--envs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cuda",
    )
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    env = SubprocVecEnv(
        [
            make_env(rank, args.seed)
            for rank in range(args.envs)
        ],
        start_method="forkserver",
    )

    env = VecNormalize(
        env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        clip_reward=10.0,
        gamma=0.99,
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=max(50_000 // args.envs, 1),
        save_path=str(CHECKPOINT_DIR),
        name_prefix="stand_ppo",
        save_vecnormalize=True,
    )

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
        ent_coef=0.0,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs={
            "log_std_init": -1.5,
            "net_arch": {
                "pi": [256, 256],
                "vf": [256, 256],
            }
        },
        tensorboard_log=str(RUN_DIR / "tensorboard"),
        device=args.device,
        seed=args.seed,
        verbose=1,
    )

    model.learn(
        total_timesteps=args.steps,
        callback=checkpoint_callback,
        tb_log_name="rocker32",
    )

    model.save(RUN_DIR / "stand_ppo_final")
    env.save(RUN_DIR / "vecnormalize.pkl")
    env.close()

    print("\nTraining complete")
    print("Model:", RUN_DIR / "stand_ppo_final.zip")
    print("Normalization:", RUN_DIR / "vecnormalize.pkl")


if __name__ == "__main__":
    main()
