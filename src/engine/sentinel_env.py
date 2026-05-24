import os
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import joblib
from engine.reward import SovereignRewardEngine
from engine.risk import GlobalRiskController
from engine.audit import ATCCAuditAgent
from engine.sim import simulate_trade

class BTCSovereignV5(gym.Env):
    def __init__(self, df):
        super().__init__()
        self.df = df.dropna().reset_index(drop=True)
        
        if 'Price' not in self.df.columns and 'Close' in self.df.columns:
            self.df = self.df.rename(columns={'Close': 'Price'})
            
        self.reward_engine = SovereignRewardEngine()
        
        # INCREASED TO 10% FOR TRAINING ROOM
        self.risk_controller = GlobalRiskController(max_drawdown_limit=0.20, session_drawdown_limit=0.10)
        self.audit_agent = ATCCAuditAgent()
        
        self.total_steps = 0
        self.episodes_completed = 0
        
        regime_path = os.path.expanduser('~/btc_ai/opt/market_genres.pkl')
        try:
            self.regime_model = joblib.load(regime_path)
            self.has_regime = True
        except Exception as e:
            self.has_regime = False
        
        drop_cols = ['Date','Open','High','Low','Price','index','1H_Open','1H_High','1H_Low','1H_Price','4H_Open','4H_High','4H_Low','4H_Price']
        self.raw_feat = self.df.drop(columns=drop_cols, errors='ignore').values.astype(np.float32)
        self.prices = self.df['Price'].values.astype(np.float32)
        self.highs = self.df['High'].values.astype(np.float32)
        self.lows = self.df['Low'].values.astype(np.float32)
        
        if '4H_Macro_Trend' in self.df.columns:
            self.trend_4h = self.df['4H_Macro_Trend'].values.astype(np.float32)
        elif 'Macro_Trend' in self.df.columns:
            self.trend_4h = self.df['Macro_Trend'].values.astype(np.float32)
        else:
            self.trend_4h = np.ones(len(self.df), dtype=np.float32)
            
        self.atr = self.df['ATR'].values.astype(np.float32)
        
        self.max_steps = len(self.df)
        self.stack_size = 4
        self.feat_dim = self.raw_feat.shape[1] + 2 
        self.observation_space = spaces.Box(low=-5.0, high=5.0, shape=(self.feat_dim * self.stack_size,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        self.history = []

    def _get_single_obs(self, idx):
        win = self.raw_feat[max(0, idx-200):idx+1]
        mean, std = np.mean(win, axis=0), np.std(win, axis=0) + 1e-8
        stat_feat = np.clip((self.raw_feat[idx] - mean) / std, -5.0, 5.0)
        curriculum_lvl = min(13, (self.total_steps // 1000000) + 1)
        return np.concatenate([stat_feat, [curriculum_lvl / 13.0], [0.0]])

    def step(self, action):
        self.total_steps += 1
        act = float(action[0])
        curriculum_lvl = min(13, (self.total_steps // 1000000) + 1)
        info = {}
        
        is_safe = self.risk_controller.update_and_check(self.balance)
        if not is_safe:
            done = True
            info['episode_report'] = {'trades': self.ep_trades, 'wins': self.ep_wins, 'ep_reward': self.ep_reward, 'final_balance': self.balance}
            return np.concatenate(self.history), -10.0, done, False, info

        if abs(act) < 0.10: # Lowered further to get it in the game
            self.current_step += 1
            self.history.pop(0)
            self.history.append(self._get_single_obs(min(self.current_step, self.max_steps-1)))
            fiat_penalty = -0.01 
            self.ep_reward += fiat_penalty
            done = self._check_done()
            if done:
                info['episode_report'] = {'trades': self.ep_trades, 'wins': self.ep_wins, 'ep_reward': self.ep_reward, 'final_balance': self.balance}
            return np.concatenate(self.history), fiat_penalty, done, False, info

        sig_id = self.audit_agent.log_signal(0, abs(act), "LONG" if act > 0 else "SHORT", self.raw_feat[self.current_step])
        ret, dur, reason = simulate_trade(self.current_step, act, self.prices, self.highs, self.lows, self.trend_4h, self.atr, self.max_steps)
        
        self.ep_trades += 1
        if ret > 0: self.ep_wins += 1

        conviction = min(abs(act), 0.50)
        pos_size = self.balance * conviction
        
        tid = self.audit_agent.log_trade_entry(sig_id, (1 if act > 0 else -1), self.prices[self.current_step], pos_size, 0, 0)
        self.audit_agent.log_trade_exit(tid, self.prices[self.current_step]*(1+ret), reason)

        adv_15m = self.df.iloc[self.current_step].get('Volume', 1.0)
        rew = float(self.reward_engine.compute_reward(ret, act, pos_size, adv_15m, curriculum_lvl))
        
        self.ep_reward += rew
        self.balance += (pos_size * ret)
        self.current_step += dur
        
        done = self._check_done()
        if done:
            info['episode_report'] = {'trades': self.ep_trades, 'wins': self.ep_wins, 'ep_reward': self.ep_reward, 'final_balance': self.balance}
        
        self.history = [self._get_single_obs(max(0, self.current_step - i)) for i in range(3, -1, -1)]
        return np.concatenate(self.history), rew, done, False, info

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.reward_engine.reset()
        self.risk_controller.reset_global()
        self.episodes_completed += 1
        self.current_step = np.random.randint(200, self.max_steps - 30000)
        self.ep_trades = 0
        self.ep_wins = 0
        self.ep_reward = 0.0
        self.start_cap = 100000.0 
        self.balance = self.start_cap
        self.history = [self._get_single_obs(self.current_step - i) for i in range(3, -1, -1)]
        return np.concatenate(self.history), {}

    def _check_done(self):
        return self.current_step >= self.max_steps - 3000
