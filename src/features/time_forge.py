import pandas as pd
import os
import glob
import time

RAW_DIR = '/home/aaiaqbtb/btc_ai/data/raw/'
OUTPUT_DIR = '/home/aaiaqbtb/btc_ai/data/processed/'

def forge_timeframes():
    print("[SYSTEM] Initiating Temporal Sanitization & Gap-Healing...")
    start_time = time.time()
    all_files = glob.glob(os.path.join(RAW_DIR, '*.csv'))
    
    if not all_files:
        print(f"[ERROR] No raw files found in {RAW_DIR}")
        return

    col_names = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.concat([pd.read_csv(f, sep=';', header=None, names=col_names) for f in all_files], ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d %H%M%S')
    df.set_index('Date', inplace=True)
    df = df[~df.index.duplicated(keep='last')].sort_index()

    # Healing the 8-day annual gaps
    full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq='1min')
    df = df.reindex(full_index)
    df['Volume'] = df['Volume'].fillna(0)
    df['Close'] = df['Close'].interpolate(method='linear')
    for col in ['Open', 'High', 'Low']:
        df[col] = df[col].fillna(df['Close'])

    agg_rules = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
    for name, tf in {'15m': '15min', '1h': '1h', '4h': '4h'}.items():
        resampled = df.resample(tf, label='right', closed='right').agg(agg_rules).dropna()
        resampled.reset_index().to_parquet(os.path.join(OUTPUT_DIR, f'btc_ohlcv_{name}.parquet'), index=False)
    
    print(f"[SUCCESS] Forge complete in {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    forge_timeframes()
