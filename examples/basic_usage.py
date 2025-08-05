from pg2ch import PostgreSQLParser, convert_ddl, validate_clickhouse_ddl_with_local

postgres_ddl = """
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

"""

parser = PostgreSQLParser()
tables = parser.parse_ddl(postgres_ddl)

print("===== PostgreSQL Table Extracted =====")
print(tables[0])

clickhouse_ddl = convert_ddl(postgres_ddl)

print("\n\n===== ClickHouse Table Converted =====")
print(clickhouse_ddl)
is_valid, message = validate_clickhouse_ddl_with_local(clickhouse_ddl)
print(message)  # ✅ DDL is valid
