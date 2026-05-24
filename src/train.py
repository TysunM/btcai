import os
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
from engine.sentinel_env import BTCSovereignV5

# --- CONFIG
BASE_DIR = os.path.expanduser('~/btc_ai')
INPUT_FILE = os.path.join(BASE_DIR, 'data/processed/rl_mtf_master.parquet')
LOG_DIR = os.path.join(BASE_DIR, 'src/logs/')
MODEL_PATH = os.path.join(BASE_DIR, 'src/models/sovereign_v5_level1.zip')

class LiveDashboardLogger(BaseCallback):
    def __init__(self, starting_capital=100000.0):
        super().__init__()
        self.starting_capital = starting_capital
        self.cumulative_capital = starting_capital
        self.global_peak = starting_capital
        self.max_drawdown = 0.0
        self.episodes_completed = 0
        self.total_trades = 0
        self.total_wins = 0

    def _on_step(self) -> bool:
        if self.locals["dones"][0]:
            self.episodes_completed += 1
            info = self.locals["infos"][0]
            
            if "episode_report" in info:
                report = info["episode_report"]
                final_balance = report.get('final_balance', self.starting_capital)
                
                # Update Trade Stats
                self.total_trades += report.get("trades", 0)
                self.total_wins += report.get("wins", 0)
                
                # Update Cumulative Capital Curve
                profit = final_balance - self.starting_capital
                self.cumulative_capital += profit
                
                if self.cumulative_capital > self.global_peak:
                    self.global_peak = self.cumulative_capital
                
                dd = (self.global_peak - self.cumulative_capital) / max(self.global_peak, 1.0)
                self.max_drawdown = max(self.max_drawdown, dd)
                
                win_rate = (self.total_wins / self.total_trades * 100) if self.total_trades > 0 else 0.0
                cumul_roi = ((self.cumulative_capital - self.starting_capital) / self.starting_capital) * 100

                # Log to TensorBoard
                self.logger.record("1_Cumulative/1_Capital", self.cumulative_capital)
                self.logger.record("1_Cumulative/2_ROI_Percent", cumul_roi)
                self.logger.record("1_Cumulative/3_Win_Rate_Percent", win_rate)
                self.logger.record("1_Cumulative/6_Max_Drawdown_Percent", self.max_drawdown * 100)
                self.logger.dump(self.num_timesteps)

                print(f"[EP {self.episodes_completed}] ROI: {cumul_roi:.2f}% | Cap: ${self.cumulative_capital:,.0f} | Win%: {win_rate:.1f}%")
        return True

def train_level1():
    print("[SYSTEM] Starting Level 1: Increased Session Leash")
    df = pd.read_parquet(INPUT_FILE)
    raw_env = DummyVecEnv([lambda: BTCSovereignV5(df)])
    env = VecNormalize(raw_env, norm_obs=True, norm_reward=False, clip_obs=5.0)
    
    model = PPO("MlpPolicy", env, verbose=0, learning_rate=3e-4, n_steps=2048, batch_size=512, ent_coef=0.03, device="cuda", tensorboard_log=LOG_DIR)
    model.learn(total_timesteps=1000000, callback=LiveDashboardLogger(), progress_bar=True)
    model.save(MODEL_PATH)
    env.save(MODEL_PATH.replace('.zip', '_vecnorm.pkl'))

if __name__ == "__main__":
    train_level1()
