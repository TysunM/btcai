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
        self.reward_engine = SovereignRewardEngine()
        self.risk_controller = GlobalRiskController()
        self.audit_agent = ATCCAuditAgent()
        self.total_steps = 0
        
        try:
            self.regime_model = joblib.load('/btc_quant/opt/market_genres.pkl')
            self.has_regime = True
        except:
            self.has_regime = False
        
        drop_cols = ['Date','Open','High','Low','Price','index','1H_Open','1H_High','1H_Low','1H_Price','4H_Open','4H_High','4H_Low','4H_Price']
        self.raw_feat = self.df.drop(columns=drop_cols, errors='ignore').values.astype(np.float32)
        self.prices = self.df['Price'].values.astype(np.float32)
        self.highs = self.df['High'].values.astype(np.float32)
        self.lows = self.df['Low'].values.astype(np.float32)
        self.trend_4h = self.df['4H_Macro_Trend'].values.astype(np.float32)
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
        lvl = (self.total_steps // 1000000 + 1) / 13.0
        reg = float(self.regime_model['gmm'].predict(self.raw_feat[idx].reshape(1, -1))[0]) / 6.0 if self.has_regime else 0.0
        return np.concatenate([stat_feat, [lvl], [reg]])

    def step(self, action):
        self.total_steps += 1
        act = float(action[0])
        
        if abs(act) >= 0.50 and not self.risk_controller.check_system_status():
            act = 0.0 

        if abs(act) < 0.50:
            self.current_step += 1
            self.history.pop(0)
            self.history.append(self._get_single_obs(min(self.current_step, self.max_steps-1)))
            return np.concatenate(self.history), -0.20, self._check_done(), False, {}

        # Log Signal
        sig_id = self.audit_agent.log_signal(int(self.history[-1][-1]*6), abs(act), "LONG" if act > 0 else "SHORT", self.raw_feat[self.current_step])
        
        # Use centralized simulator
        ret, dur, reason = simulate_trade(self.current_step, act, self.prices, self.highs, self.lows, self.trend_4h, self.atr, self.max_steps)
        
        # Log Trade
        tid = self.audit_agent.log_trade_entry(sig_id, (1 if act > 0 else -1), self.prices[self.current_step], self.balance*0.80, 0, 0)
        self.audit_agent.log_trade_exit(tid, self.prices[self.current_step]*(1+ret), reason)

        rew = self.reward_engine.compute_reward(ret, act, self.balance*0.80, self.df.iloc[self.current_step]['Volume'])
        self.balance += (self.balance * 0.80 * ret)
        self.current_step += dur
        
        self.history = [self._get_single_obs(max(0, self.current_step - i)) for i in range(3, -1, -1)]
        return np.concatenate(self.history), rew, self._check_done(), False, {}

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.reward_engine.reset()
        self.current_step = np.random.randint(200, self.max_steps - 30000)
        self.start_cap = 100000.0 * (2 ** (min(self.total_steps // 1000000, 12)))
        self.balance = self.start_cap
        self.history = [self._get_single_obs(self.current_step - i) for i in range(3, -1, -1)]
        return np.concatenate(self.history), {}

    def _check_done(self):
        return self.balance <= (self.start_cap * 0.5) or self.current_step >= self.max_steps - 3000
