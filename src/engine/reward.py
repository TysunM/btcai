import numpy as np

class DifferentialSharpeEngine:
    def __init__(self, eta=0.01):
        self.eta = eta
        self.A_t = 0.0
        self.B_t = 0.0
        self.initialized = False
        
    def update(self, return_t):
        if not self.initialized:
            self.A_t = return_t
            self.B_t = return_t ** 2
            self.initialized = True
            return 0.0
        
        delta_A = return_t - self.A_t
        delta_B = return_t**2 - self.B_t
        
        A_prev, B_prev = self.A_t, self.B_t
        
        numerator = B_prev * delta_A - 0.5 * A_prev * delta_B
        denominator = (B_prev - A_prev**2) ** 1.5 + 1e-8
        d_sharpe = numerator / denominator
        
        self.A_t += self.eta * delta_A
        self.B_t += self.eta * delta_B
        
        return d_sharpe

    def reset(self):
        self.A_t = 0.0
        self.B_t = 0.0
        self.initialized = False

class SovereignRewardEngine:
    def __init__(self, fee_bps=4.0, impact_coeff=0.002, lambda_turnover=0.5):
        self.ds_engine = DifferentialSharpeEngine()
        self.base_fee = fee_bps / 10000
        self.base_impact = impact_coeff
        self.lambda_turnover = lambda_turnover
        
        self.prev_action = 0.0
        self.rolling_rewards = []
        self.rolling_returns = [] 
        self.window = 500

    def compute_reward(self, trade_ret, current_action, pos_size, adv_15m, curriculum_level=1):
        # --- CURRICULUM SCALING ---
        friction_multiplier = max(0.0, min((curriculum_level - 1) / 12.0, 1.0))

        self.rolling_returns.append(trade_ret)
        if len(self.rolling_returns) > self.window:
            self.rolling_returns.pop(0)

        # 1. Differential Sharpe
        reward_ds = self.ds_engine.update(trade_ret)
        
        # 2. CVaR Penalty (95% Tail Risk)
        cvar_penalty = 0.0
        if len(self.rolling_returns) >= 50:
            var_95 = np.percentile(self.rolling_returns, 5)
            tail_losses = [r for r in self.rolling_returns if r <= var_95]
            if tail_losses:
                cvar_penalty = abs(np.mean(tail_losses)) * 0.3 
        
        # 3. Dynamic Friction
        participation_rate = pos_size / (adv_15m + 1e-8)
        impact_cost = (self.base_impact * friction_multiplier) * (participation_rate**1.5) if participation_rate > 0.01 else 0
        total_friction = ((self.base_fee * friction_multiplier) * abs(current_action)) + impact_cost
        
        # 4. Turnover & Flip Penalty (NOW PROPERLY SCALED)
        turnover_penalty = (self.lambda_turnover * friction_multiplier) * abs(current_action - self.prev_action)
        flip_penalty = (0.3 * friction_multiplier) if np.sign(current_action) != np.sign(self.prev_action) else 0.0
        
        # Combine Stack
        raw_reward = reward_ds - cvar_penalty - total_friction - turnover_penalty - flip_penalty
        
        norm_reward = self._normalize(raw_reward)
        self.prev_action = current_action
        
        return norm_reward

    def _normalize(self, reward):
        self.rolling_rewards.append(reward)
        if len(self.rolling_rewards) > self.window:
            self.rolling_rewards.pop(0)
            
        if len(self.rolling_rewards) < 50:
            return reward
            
        mean = np.mean(self.rolling_rewards)
        std = np.std(self.rolling_rewards) + 1e-8
        z_score = (reward - mean) / std
        
        return np.clip(z_score, -5.0, 5.0)

    def reset(self):
        self.ds_engine.reset()
        self.prev_action = 0.0
        self.rolling_rewards = []
        self.rolling_returns = []
