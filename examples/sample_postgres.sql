CREATE TABLE IF NOT EXISTS public.transactions (
    transaction_id    BIGSERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL,
    account_id        INTEGER NOT NULL,
    transaction_type  VARCHAR(20) NOT NULL,
    amount            DECIMAL(15,2) NOT NULL,
    currency          CHAR(3) DEFAULT 'USD',
    description       TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
