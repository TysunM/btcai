import pandas as pd
import os

PROCESSED_DIR = '/home/aaiaqbtb/btc_ai/data/processed/'
OUTPUT = os.path.join(PROCESSED_DIR, 'rl_mtf_master.parquet')

def align():
    print("[SYSTEM] Aligning Multi-Timeframe Matrix...")
    df_15m = pd.read_parquet(os.path.join(PROCESSED_DIR, 'rl_smart_money_15m.parquet')).set_index('Date')
    df_1h = pd.read_parquet(os.path.join(PROCESSED_DIR, 'rl_smart_money_1h.parquet')).set_index('Date')
    df_4h = pd.read_parquet(os.path.join(PROCESSED_DIR, 'rl_smart_money_4h.parquet')).set_index('Date')

    df_1h.columns = [f"1H_{c}" for c in df_1h.columns]
    df_4h.columns = [f"4H_{c}" for c in df_4h.columns]

    master = df_15m.join(df_1h, how='left').join(df_4h, how='left').ffill().dropna()
    master.reset_index().to_parquet(OUTPUT, index=False)
    print(f"[SUCCESS] Master Matrix Forged: {OUTPUT}")

if __name__ == "__main__": align()
