CREATE TABLE transactions (
    transaction_id Int64,
    user_id Int32,
    account_id Int32,
    transaction_type String,
    amount Decimal64(4),
    currency Nullable(String) DEFAULT 'USD',
    description Nullable(String),
    created_at Nullable(DateTime) DEFAULT NOW()
)
ENGINE = MergeTree()
ORDER BY (transaction_id)
;
