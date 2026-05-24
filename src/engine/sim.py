import numpy as np

def simulate_trade(current_step, action_val, prices, highs, lows, trend_4h, atr, max_steps):
    """
    Standardized ATCC Trade Logic:
    - Min Hold: 288 bars (3 days)
    - Max Hold: 2880 bars (30 days)
    - TP: 10.0 * ATR | SL: 3.0 * ATR
    """
    entry_p = float(prices[current_step])
    direction = 1 if action_val > 0 else -1
    current_atr = float(atr[current_step])

    tp = entry_p + (current_atr * 10.0 * direction)
    sl = entry_p - (current_atr * 3.0 * direction)

    trade_ret = 0.0
    hold_duration = 0
    exit_reason = "max_hold"

    for hold in range(1, 2880):
        idx = current_step + hold
        if idx >= max_steps:
            trade_ret = (float(prices[max_steps - 1]) - entry_p) / entry_p * direction
            hold_duration = hold
            exit_reason = "boundary"
            break

        # Institutional Floor: No exit before 3 days (288 bars)
        if hold < 288:
            continue

        h, l, c = float(highs[idx]), float(lows[idx]), float(prices[idx])

        if (direction == 1 and l <= sl) or (direction == -1 and h >= sl):
            trade_ret = (sl - entry_p) / entry_p * direction
            hold_duration = hold
            exit_reason = "stop_loss"
            break

        if (direction == 1 and h >= tp) or (direction == -1 and l <= tp):
            trade_ret = (tp - entry_p) / entry_p * direction
            hold_duration = hold
            exit_reason = "take_profit"
            break

        if trend_4h[idx] != direction:
            trade_ret = (c - entry_p) / entry_p * direction
            hold_duration = hold
            exit_reason = "trend_flip"
            break

    if hold_duration == 0:
        hold_duration = 2879
        final_idx = min(current_step + 2879, max_steps - 1)
        trade_ret = (float(prices[final_idx]) - entry_p) / entry_p * direction
        exit_reason = "max_hold"

    return trade_ret, hold_duration, exit_reason
