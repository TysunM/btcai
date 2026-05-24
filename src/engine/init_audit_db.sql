-- ATCC Institutional Audit Schema
-- Purpose: Provide an immutable ledger for every model decision

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1. Signals Log: Why the bot thought about trading
CREATE TABLE signals_log (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    regime_id INT, -- GMM Cluster
    feature_vector_hash TEXT, -- For data integrity verification
    confidence_score FLOAT, -- SignalGate threshold
    decision TEXT, -- LONG, SHORT, FLAT
    metadata JSONB -- Storage for the 28+ raw feature values
);
SELECT create_hypertable('signals_log', 'timestamp');

-- 2. Trades Log: Execution and Risk Guardrails
CREATE TABLE trades_log (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals_log(signal_id),
    entry_timestamp TIMESTAMPTZ NOT NULL,
    exit_timestamp TIMESTAMPTZ,
    direction INT, -- 1 for Long, -1 for Short
    entry_price NUMERIC,
    exit_price NUMERIC,
    position_size_usd NUMERIC,
    stop_loss_price NUMERIC,
    take_profit_price NUMERIC,
    exit_reason TEXT -- 'stop_loss', 'take_profit', 'trend_flip', 'manual'
);
SELECT create_hypertable('trades_log', 'entry_timestamp');

-- 3. Risk/System Events: Audit trail for safety failures
CREATE TABLE risk_events (
    event_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type TEXT, -- 'DRAWDOWN_CIRCUIT_BREAKER', 'MODEL_DRIFT', 'KILL_SWITCH'
    details JSONB
);
