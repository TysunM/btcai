import sqlite3
import json
from datetime import datetime
import os
import uuid

class ATCCAuditAgent:
    def __init__(self, db_path=os.path.expanduser("~/btc_ai/atcc_local_audit.db")):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals_log (
                signal_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                regime_id INTEGER,
                confidence_score REAL,
                decision TEXT,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades_log (
                trade_id TEXT PRIMARY KEY,
                signal_id TEXT,
                entry_timestamp TEXT NOT NULL,
                exit_timestamp TEXT,
                direction INTEGER,
                entry_price REAL,
                exit_price REAL,
                position_size_usd REAL,
                stop_loss_price REAL,
                take_profit_price REAL,
                exit_reason TEXT,
                FOREIGN KEY(signal_id) REFERENCES signals_log(signal_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT,
                details TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_signal(self, regime_id, confidence, decision, features):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        signal_id = str(uuid.uuid4())
        native_regime_id = int(regime_id) if regime_id is not None else None
        native_confidence = float(confidence)
        
        feat_list = features.tolist() if hasattr(features, 'tolist') else features
            
        cursor.execute("""
            INSERT INTO signals_log (signal_id, timestamp, regime_id, confidence_score, decision, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            signal_id,
            datetime.now().isoformat(), 
            native_regime_id, 
            native_confidence, 
            decision, 
            json.dumps(feat_list)
        ))
        
        conn.commit()
        conn.close()
        return signal_id

    def log_trade_entry(self, signal_id, direction, price, size, sl, tp):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        trade_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO trades_log (trade_id, signal_id, entry_timestamp, direction, entry_price, position_size_usd, stop_loss_price, take_profit_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id,
            signal_id, 
            datetime.now().isoformat(), 
            int(direction), 
            float(price), 
            float(size), 
            float(sl), 
            float(tp)
        ))
        
        conn.commit()
        conn.close()
        return trade_id

    def log_trade_exit(self, trade_id, price, reason):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE trades_log SET exit_timestamp = ?, exit_price = ?, exit_reason = ?
            WHERE trade_id = ?
        """, (
            datetime.now().isoformat(), 
            float(price), 
            str(reason), 
            trade_id
        ))
        
        conn.commit()
        conn.close()

    def log_risk_event(self, event_type, details):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO risk_events (timestamp, event_type, details) 
            VALUES (?, ?, ?)
        """, (
            datetime.now().isoformat(), 
            str(event_type), 
            json.dumps(details)
        ))
        
        conn.commit()
        conn.close()
