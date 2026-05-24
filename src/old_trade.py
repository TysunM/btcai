import pandas as pd
import numpy as np
import sys
import os
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from engine.sentinel_env import BTCSovereignSentinel

class SovereignStaircaseCallback(BaseCallback):
    def __init__(self, initial_capital, set_config, verbose=0):
        super(SovereignStaircaseCallback, self).__init__(verbose)
        self.initial_capital = initial_capital
        self.set_config = set_config
        self.rollout_count = 0
        self.current_milestone_idx = 0
        self.cumulative_steps_at_last_hardening = 0

    def _on_step(self) -> bool:
        total_steps = self.num_timesteps
        if self.current_milestone_idx < len(self.set_config):
            milestone_steps, level_name = self.set_config[self.current_milestone_idx]
            if total_steps >= milestone_steps and total_steps > self.cumulative_steps_at_last_hardening:
                self.cumulative_steps_at_last_hardening = total_steps
                self.current_milestone_idx += 1
                # Difficulty scaling would go here if needed
                print(f"\n[SYSTEM] FORGE HARDENING: Advancing to {level_name}", flush=True)
        return True

    def _on_rollout_end(self) -> None:
        current_balance = self.training_env.get_attr("balance")[0]
        mdd_val = self.training_env.get_attr("max_drawdown")[0]
        sharpe_val = self.training_env.get_attr("sharpe")[0] 
        
        roi = ((current_balance - self.initial_capital) / self.initial_capital) * 100
        self.rollout_count += 1
        
        print(f"\n$$$    Starting Capital = ${self.initial_capital:,.2f}    $$$")
        print(f"after {self.rollout_count} rollouts:")
        print(f"$$$    Account Balance: = ${current_balance:,.2f} $$$")
        print(f"%%  ROI = {roi:.2f}%  |  MDD = {mdd_val*100:.2f}%  |  SHARPE = {sharpe_val:.2f}  %%")
        print("-" * 55, flush=True)

def train_sovereign(set_num):
    df = pd.read_parquet('/home/aaiaqbtb/btc_ai/data/processed/rl_mtf_master.parquet')
    current_capital = 3000000.0
    
    configs = {
        1: [(1000000, "LEVEL 1"), (2000000, "LEVEL 2"), (3000000, "LEVEL 3")],
    }
    
    set_config = configs[set_num]
    total_set_steps = set_config[-1][0]
    
    print(f"\n[INIT] Starting Sovereign Institutional Run | Floor: 4.5%", flush=True)
    
    env = BTCSovereignSentinel(df, initial_balance=current_capital)
    model = PPO("MlpPolicy", env, learning_rate=0.00004, verbose=1, device="auto")
    callback = SovereignStaircaseCallback(initial_capital=current_capital, set_config=set_config)

    try:
        model.learn(total_timesteps=total_set_steps, callback=callback)
        model.save(f"models/sovereign_set{set_num}_institutional")
    except KeyboardInterrupt:
        model.save(f"models/sovereign_checkpoint")

if __name__ == "__main__":
    train_sovereign(set_num=1)
