import pandas as pd
import numpy as np
import os
from numba import jit

@jit(nopython=True)
def fast_ehlers_dc(src_arr, window=21):
    n = len(src_arr)
    hp = np.zeros(n)
    dc = np.full(n, float(window))
    w = 1.414 * 3.14159 / window
    q = np.exp(-w)
    c1, c2 = 2.0 * q * np.cos(w), q * q
    a0 = 0.25 * (1.0 + c1 + c2)
    for i in range(2, n):
        hp[i] = a0 * (src_arr[i] - 2*src_arr[i-1] + src_arr[i-2]) + c1*hp[i-1] - c2*hp[i-2]
    for i in range(window * 2, n):
        x = hp[i-window+1: i+1]
        best_corr = -1.0
        best_lag = window
        for lag in range(2, window + 1):
            y = hp[i-window+1-lag: i+1-lag]
            dot = np.dot(x, y)
            mag = np.sqrt(np.dot(x, x) * np.dot(y, y))
            corr = dot / (mag + 1e-10)
            if corr > best_corr:
                best_corr = corr
                best_lag = lag
        dc[i] = best_lag * 2.0
    return dc

def build_matrix_for_timeframe(tf):
    input_file = f'/btc_quant/data/processed/btc_ohlcv_{tf}.parquet'
    output_file = f'/btc_quant/data/processed/rl_smart_money_{tf}.parquet'
    
    if not os.path.exists(input_file):
        return

    df = pd.read_parquet(input_file)
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1)).fillna(0.0)
    
    # --- VOLATILITY & ENTROPY CHANNELS ---
    # Rolling 100-period Volatility Z-Score (Stationary Entropy)
    df['Vol_Raw'] = df['Log_Returns'].rolling(window=100).std()
    df['Vol_Z'] = (df['Vol_Raw'] - df['Vol_Raw'].rolling(200).mean()) / (df['Vol_Raw'].rolling(200).std() + 1e-10)
    
    # Relative Volume (RVOL) - Institutional Accumulation Detector
    df['RVOL'] = df['Volume'] / (df['Volume'].rolling(window=50).mean() + 1e-10)
    
    # --- CORE INDICATORS ---
    df['TR'] = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = df['TR'].rolling(15).mean()
    df['Volume_Z'] = (df['Volume'] - df['Volume'].rolling(60).mean()) / (df['Volume'].rolling(60).std() + 1e-10)
    
    delta = df['Close'].diff()
    gain, loss = (delta.where(delta > 0, 0)).rolling(15).mean(), (-delta.where(delta < 0, 0)).rolling(15).mean()
    df['RSI_15'] = 100-(100/(1+ (gain / (loss + 1e-10))))
    
    df['VWAP'] = (((df['High'] + df['Low'] + df['Close']) / 3) * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-10)
    df['VWAP_Dev'] = (df['Close'] - df['VWAP']) / (df['VWAP'] + 1e-10)
    
    df['Macro_Trend'] = np.where(df['Close'] > df['Close'].ewm(span=210, adjust=False).mean(), 1, -1)
    
    roll_max, roll_min = df['High'].rolling(21).max(), df['Low'].rolling(21).min()
    swing = roll_max - roll_min + 1e-10
    df['Fib_618'] = (df['Close'] - (roll_max - (swing * 0.618))) / swing
    
    df['EMF_Frequency'] = fast_ehlers_dc(df['Close'].values)
    df['Liq_Exhaustion'] = (df['Volume'] * df['Log_Returns'].abs()) / (df['ATR'] + 1e-10)
    
    df = df.dropna()
    feature_cols = ['Log_Returns', 'ATR', 'Volume_Z', 'RSI_15', 'VWAP_Dev', 'Macro_Trend', 'Fib_618', 'EMF_Frequency', 'Liq_Exhaustion', 'Vol_Z', 'RVOL']
    
    df = df.rename(columns={'Close': 'Price'}).reset_index()
    output_cols = ['Date', 'Open', 'High', 'Low', 'Price'] + feature_cols
    df[output_cols].to_parquet(output_file, index=False)

if __name__ == "__main__":
    for timeframe in ['15m', '1h', '4h']:
        build_matrix_for_timeframe(timeframe)
