
-- ============================================
-- AI PROMPT FIREWALL
-- Database Schema
-- Database: prompt_firewall_db
-- ============================================


-- TABLE 1: USERS
-- Stores application user information

CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    -- Store a secure hash of the API key, never plaintext
    api_key TEXT NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- TABLE 2: PROMPT AUDIT LOGS
-- Stores every submitted prompt and its security decision

CREATE TABLE IF NOT EXISTS prompt_audit_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    user_id BIGINT NOT NULL,

    raw_prompt TEXT NOT NULL,

    sanitized_prompt TEXT,

    risk_status VARCHAR(20) NOT NULL,

    block_reason TEXT,

    ai_response TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Connect each transaction to its user
    CONSTRAINT fk_prompt_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT,

    -- Only allow these three security decisions
    CONSTRAINT chk_risk_status
        CHECK (risk_status IN ('SAFE', 'BLOCKED', 'FLAGGED'))
);


-- INDEXES
-- Improve audit log filtering and retrieval performance

CREATE INDEX IF NOT EXISTS idx_audit_user_id
    ON prompt_audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_risk_status
    ON prompt_audit_logs(risk_status);

CREATE INDEX IF NOT EXISTS idx_audit_created_at
    ON prompt_audit_logs(created_at DESC);


-- ============================================
-- END OF DATABASE SCHEMA
-- ============================================
