-- ============================================================
-- FINANCIAL FRAUD DETECTION SYSTEM
-- DATABASE SCHEMA
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- USERS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL UNIQUE,

    password TEXT NOT NULL,

    role TEXT NOT NULL DEFAULT 'admin',

    created_at TEXT NOT NULL
);


-- ============================================================
-- TRANSACTIONS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    transaction_id TEXT NOT NULL UNIQUE,

    transaction_time TEXT NOT NULL,

    customer_id TEXT,

    merchant_id TEXT,

    transaction_amount REAL NOT NULL,

    payment_channel TEXT,

    device_type TEXT,

    is_international INTEGER DEFAULT 0,

    account_age_days REAL,

    credit_score_band INTEGER,

    kyc_level INTEGER,

    avg_monthly_spend REAL,

    merchant_risk_score REAL,

    ip_risk_score REAL,

    txn_count_1h INTEGER DEFAULT 0,

    txn_count_24h INTEGER DEFAULT 0,

    failed_txn_count_24h INTEGER DEFAULT 0,

    geo_distance_from_last_txn REAL,

    amount_deviation_from_user_mean REAL,

    fraud_probability REAL,

    predicted_fraud INTEGER DEFAULT 0,

    risk_level TEXT,

    risk_reasons TEXT,

    recommended_action TEXT,

    actual_fraud INTEGER,

    review_status TEXT DEFAULT 'Pending',

    reviewed_by TEXT,

    review_notes TEXT,

    created_at TEXT NOT NULL
);


-- ============================================================
-- ALERTS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS alerts (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    transaction_id TEXT NOT NULL,

    alert_type TEXT NOT NULL,

    risk_level TEXT NOT NULL,

    message TEXT,

    status TEXT DEFAULT 'Open',

    created_at TEXT NOT NULL,

    resolved_at TEXT,

    resolved_by TEXT,

    FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE CASCADE
);


-- ============================================================
-- MODEL LOGS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS model_logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    transaction_id TEXT,

    model_name TEXT NOT NULL,

    fraud_probability REAL,

    prediction INTEGER,

    risk_level TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE SET NULL
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_transaction_time
ON transactions(transaction_time);


CREATE INDEX IF NOT EXISTS idx_transaction_risk
ON transactions(risk_level);


CREATE INDEX IF NOT EXISTS idx_transaction_prediction
ON transactions(predicted_fraud);


CREATE INDEX IF NOT EXISTS idx_transaction_customer
ON transactions(customer_id);


CREATE INDEX IF NOT EXISTS idx_transaction_merchant
ON transactions(merchant_id);


CREATE INDEX IF NOT EXISTS idx_alert_status
ON alerts(status);


CREATE INDEX IF NOT EXISTS idx_alert_transaction
ON alerts(transaction_id);


CREATE INDEX IF NOT EXISTS idx_model_transaction
ON model_logs(transaction_id);