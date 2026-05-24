CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE signals_log (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    regime_id INT,
    feature_vector_hash TEXT,
    confidence_score FLOAT,
    decision TEXT,
    metadata JSONB
);
SELECT create_hypertable('signals_log', 'timestamp');

CREATE TABLE trades_log (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals_log(signal_id),
    entry_timestamp TIMESTAMPTZ NOT NULL,
    exit_timestamp TIMESTAMPTZ,
    direction INT,
    entry_price NUMERIC,
    exit_price NUMERIC,
    position_size_usd NUMERIC,
    stop_loss_price NUMERIC,
    take_profit_price NUMERIC,
    exit_reason TEXT
);
SELECT create_hypertable('trades_log', 'entry_timestamp');

CREATE TABLE risk_events (
    event_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type TEXT,
    details JSONB
);
