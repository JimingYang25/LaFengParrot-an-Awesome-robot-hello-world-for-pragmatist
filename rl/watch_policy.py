import time
from pathlib import Path

import mujoco
import mujoco.viewer
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl.lafengparrot_env import LaFengParrotStandEnv


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "rl" / "runs" / "stand_ppo_rocker32"


def main():
    raw_env = LaFengParrotStandEnv()
    vec_env = DummyVecEnv([lambda: Monitor(raw_env)])
    vec_env = VecNormalize.load(
        RUN_DIR / "vecnormalize.pkl",
        vec_env,
    )
    vec_env.training = False
    vec_env.norm_reward = False

    model = PPO.load(
        RUN_DIR / "stand_ppo_final.zip",
        env=vec_env,
        device="cpu",
    )

    obs = vec_env.reset()
    episode = 1
    episode_reward = 0.0
    control_dt = raw_env.model.opt.timestep * raw_env.frame_skip

    with mujoco.viewer.launch_passive(raw_env.model, raw_env.data) as viewer:
        viewer.cam.lookat[:] = [0.0, 0.0, 0.10]
        viewer.cam.distance = 0.55
        viewer.cam.azimuth = 150
        viewer.cam.elevation = -15

        while viewer.is_running():
            frame_start = time.perf_counter()

            action, _ = model.predict(obs, deterministic=True)
            obs, reward, dones, infos = vec_env.step(action)
            episode_reward += float(reward[0])

            if bool(dones[0]):
                info = infos[0]
                fell = not bool(info.get("TimeLimit.truncated", False))
                length = int(info["episode"]["l"])
                print(
                    f"episode={episode} steps={length} "
                    f"reward={episode_reward:.1f} fell={fell}",
                    flush=True,
                )
                episode += 1
                episode_reward = 0.0

            viewer.sync()
            remaining = control_dt - (time.perf_counter() - frame_start)
            if remaining > 0.0:
                time.sleep(remaining)

    vec_env.close()


if __name__ == "__main__":
    main()
