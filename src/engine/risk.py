class GlobalRiskController:
    """Institutional Risk Manager: High-Water Marks & Circuit Breakers"""
    def __init__(self, max_drawdown_limit=0.20, session_drawdown_limit=0.03):
        self.max_dd_limit = max_drawdown_limit
        self.session_dd_limit = session_drawdown_limit
        
        self.peak_capital = 0.0
        self.session_start_capital = 0.0
        self.system_halted = False
        self.halt_reason = ""

    def update_and_check(self, current_capital) -> bool:
        """Returns True if safe to trade, False if circuit breaker is triggered."""
        if self.peak_capital == 0.0:
            self.peak_capital = current_capital
            self.session_start_capital = current_capital

        # Update High-Water Mark (Peak Equity)
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
            
        # Calculate Drawdowns
        global_dd = (self.peak_capital - current_capital) / self.peak_capital
        session_dd = (self.session_start_capital - current_capital) / max(self.session_start_capital, 1.0)

        # Enforce Circuit Breakers
        if global_dd >= self.max_dd_limit:
            self.system_halted = True
            self.halt_reason = f"MAX_DRAWDOWN_BREACH_{global_dd*100:.1f}PCT"
            return False

        if session_dd >= self.session_dd_limit:
            self.system_halted = True
            self.halt_reason = f"SESSION_DRAWDOWN_BREACH_{session_dd*100:.1f}PCT"
            return False

        self.system_halted = False
        return True

    def reset_session(self, current_capital):
        """Called periodically (e.g., daily) to reset session limits."""
        self.session_start_capital = current_capital
        if self.halt_reason.startswith("SESSION"):
            self.system_halted = False
            self.halt_reason = ""

    def reset_global(self):
        """Called on full environment reset."""
        self.peak_capital = 0.0
        self.session_start_capital = 0.0
        self.system_halted = False
        self.halt_reason = ""
