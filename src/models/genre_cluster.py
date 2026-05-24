import os, pandas as pd, numpy as np, joblib
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

# RYZEN 9HX DEADLOCK FIX
os.environ["OMP_NUM_THREADS"] = "4"

def cluster():
    print("[SYSTEM] Sculpting 6 Market Genres...")
    df = pd.read_parquet('/home/aaiaqbtb/btc_ai/data/processed/rl_smart_money_4h.parquet')
    
    # Strictly isolate only numeric columns
    # This automatically drops 'Date' or any other non-math columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Define features to use (all numeric columns)
    feats = numeric_df.columns.tolist()
    
    scaler = StandardScaler()
    data = scaler.fit_transform(numeric_df.values)
    
    # Identifying 6 Institutional Regimes
    gmm = GaussianMixture(n_components=6, covariance_type='full', random_state=42).fit(data)
    
    # Save artifacts to /opt/
    os.makedirs('/home/aaiaqbtb/btc_ai/opt/', exist_ok=True)
    joblib.dump({'gmm': gmm, 'scaler': scaler, 'feats': feats}, '/home/aaiaqbtb/btc_ai/opt/market_genres.pkl')
    print("[SUCCESS] Genre Engine Saved to /opt/")

if __name__ == "__main__":
    cluster()
