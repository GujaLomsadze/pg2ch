# tests/test_transactions_table.py
"""
Test for transactions table parsing and conversion
Validates complex PostgreSQL DDL with constraints, defaults, and various data types
"""

import pytest

from pg2ch import PostgreSQLParser, convert_ddl


def test_transactions_table_parsing():
    """Test that transactions table is parsed correctly"""

    postgres_ddl = """
    CREATE TABLE IF NOT EXISTS public.transactions (
        transaction_id    BIGSERIAL PRIMARY KEY,
        user_id           INTEGER NOT NULL,
        account_id        INTEGER NOT NULL,
        transaction_type  VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer', 'payment')),
        amount            DECIMAL(15,2) NOT NULL,
        currency          CHAR(3) DEFAULT 'USD',
        description       TEXT,
        reference_id      VARCHAR(100) UNIQUE,
        status            VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
        merchant_id       INTEGER,
        payment_method    VARCHAR(50),
        fee_amount        DECIMAL(10,2) DEFAULT 0.00,
        exchange_rate     DECIMAL(10,6),
        metadata          JSONB,
        ip_address        INET,
        user_agent        TEXT,
        created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        processed_at      TIMESTAMP WITH TIME ZONE
    );
    """

    # Parse the DDL
    parser = PostgreSQLParser()
    tables = parser.parse_ddl(postgres_ddl)

    # Basic table validation
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"

    table = tables[0]
    assert (
        table.name == "transactions"
    ), f"Expected table name 'transactions', got '{table.name}'"
    assert len(table.columns) == 19, f"Expected 19 columns, got {len(table.columns)}"
    assert table.primary_keys == [
        "transaction_id"
    ], f"Expected primary key 'transaction_id', got {table.primary_keys}"

    # Column-specific validations
    columns_by_name = {col.name: col for col in table.columns}

    # Test transaction_id (BIGSERIAL PRIMARY KEY)
    transaction_id = columns_by_name["transaction_id"]
    assert transaction_id.data_type == "bigint"
    assert transaction_id.primary_key == True
    assert (
        transaction_id.nullable == True
    )  # Note: SERIAL is technically nullable in our mapping

    # Test user_id (INTEGER NOT NULL)
    user_id = columns_by_name["user_id"]
    assert user_id.data_type == "integer"
    assert user_id.nullable == False
    assert user_id.primary_key == False

    # Test transaction_type (VARCHAR with CHECK constraint)
    transaction_type = columns_by_name["transaction_type"]
    assert transaction_type.data_type == "string"
    assert transaction_type.nullable == False

    # Test amount (DECIMAL NOT NULL)
    amount = columns_by_name["amount"]
    assert amount.data_type == "decimal"
    assert amount.nullable == False

    # Test currency (CHAR with DEFAULT)
    currency = columns_by_name["currency"]
    assert currency.data_type == "string"  # CHAR maps to string
    assert currency.default == "'USD'"

    # Test reference_id (VARCHAR UNIQUE)
    reference_id = columns_by_name["reference_id"]
    assert reference_id.data_type == "string"
    assert reference_id.unique == True

    # Test status (VARCHAR with DEFAULT and CHECK)
    status = columns_by_name["status"]
    assert status.data_type == "string"
    assert status.default == "'pending'"

    # Test fee_amount (DECIMAL with DEFAULT)
    fee_amount = columns_by_name["fee_amount"]
    assert fee_amount.data_type == "decimal"
    assert fee_amount.default == "0.00"

    # Test metadata (JSONB)
    metadata = columns_by_name["metadata"]
    assert metadata.data_type == "string"  # JSONB maps to string

    # Test timestamp fields
    created_at = columns_by_name["created_at"]
    assert created_at.data_type == "datetime"
    assert created_at.default == "NOW()"  # CURRENT_TIMESTAMP converted

    updated_at = columns_by_name["updated_at"]
    assert updated_at.data_type == "datetime"
    assert updated_at.default == "NOW()"

    processed_at = columns_by_name["processed_at"]
    assert processed_at.data_type == "datetime"
    assert processed_at.default is None

    print("✅ All column parsing tests passed!")


def test_transactions_table_conversion():
    """Test that transactions table converts to valid ClickHouse DDL"""

    postgres_ddl = """
    CREATE TABLE IF NOT EXISTS public.transactions (
        transaction_id    BIGSERIAL PRIMARY KEY,
        user_id           INTEGER NOT NULL,
        account_id        INTEGER NOT NULL,
        transaction_type  VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer', 'payment')),
        amount            DECIMAL(15,2) NOT NULL,
        currency          CHAR(3) DEFAULT 'USD',
        description       TEXT,
        reference_id      VARCHAR(100) UNIQUE,
        status            VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
        merchant_id       INTEGER,
        payment_method    VARCHAR(50),
        fee_amount        DECIMAL(10,2) DEFAULT 0.00,
        exchange_rate     DECIMAL(10,6),
        metadata          JSONB,
        ip_address        INET,
        user_agent        TEXT,
        created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        processed_at      TIMESTAMP WITH TIME ZONE
    );
    """

    # Convert to ClickHouse
    clickhouse_ddl = convert_ddl(postgres_ddl)

    # Basic structure tests
    assert "CREATE TABLE" in clickhouse_ddl
    assert "transactions" in clickhouse_ddl
    assert "ENGINE = MergeTree()" in clickhouse_ddl
    assert "ORDER BY (transaction_id)" in clickhouse_ddl
    assert clickhouse_ddl.strip().endswith(";")

    # Data type conversion tests
    assert "transaction_id Int64" in clickhouse_ddl  # BIGSERIAL -> Int64
    assert "user_id Int32" in clickhouse_ddl  # INTEGER -> Int32
    assert "transaction_type String" in clickhouse_ddl  # VARCHAR -> String
    assert "amount Decimal64(4)" in clickhouse_ddl  # DECIMAL -> Decimal64(4)
    assert "metadata Nullable(String)" in clickhouse_ddl  # JSONB -> Nullable(String)

    # Default value conversion tests
    assert "DEFAULT 'USD'" in clickhouse_ddl
    assert "DEFAULT 'pending'" in clickhouse_ddl
    assert "DEFAULT 0.00" in clickhouse_ddl
    assert "DEFAULT NOW()" in clickhouse_ddl  # CURRENT_TIMESTAMP converted

    # Nullable handling tests
    assert "user_id Int32," in clickhouse_ddl  # NOT NULL columns shouldn't be Nullable
    assert "transaction_type String," in clickhouse_ddl  # NOT NULL
    assert "amount Decimal64(4)," in clickhouse_ddl  # NOT NULL
    assert "description Nullable(String)" in clickhouse_ddl  # Nullable columns
    assert "merchant_id Nullable(Int32)" in clickhouse_ddl

    print("✅ All conversion tests passed!")
    print(f"✅ Generated DDL length: {len(clickhouse_ddl)} characters")


def test_specific_column_presence():
    """Test that all expected columns are present in conversion"""

    postgres_ddl = """
    CREATE TABLE IF NOT EXISTS public.transactions (
        transaction_id    BIGSERIAL PRIMARY KEY,
        user_id           INTEGER NOT NULL,
        account_id        INTEGER NOT NULL,
        transaction_type  VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer', 'payment')),
        amount            DECIMAL(15,2) NOT NULL,
        currency          CHAR(3) DEFAULT 'USD',
        description       TEXT,
        reference_id      VARCHAR(100) UNIQUE,
        status            VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
        merchant_id       INTEGER,
        payment_method    VARCHAR(50),
        fee_amount        DECIMAL(10,2) DEFAULT 0.00,
        exchange_rate     DECIMAL(10,6),
        metadata          JSONB,
        ip_address        INET,
        user_agent        TEXT,
        created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        processed_at      TIMESTAMP WITH TIME ZONE
    );
    """

    expected_columns = [
        "transaction_id",
        "user_id",
        "account_id",
        "transaction_type",
        "amount",
        "currency",
        "description",
        "reference_id",
        "status",
        "merchant_id",
        "payment_method",
        "fee_amount",
        "exchange_rate",
        "metadata",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
        "processed_at",
    ]

    clickhouse_ddl = convert_ddl(postgres_ddl)

    for column in expected_columns:
        assert (
            column in clickhouse_ddl
        ), f"Column '{column}' not found in ClickHouse DDL"

    print(f"✅ All {len(expected_columns)} expected columns found in DDL")


def test_edge_cases():
    """Test edge cases in the transactions table"""

    postgres_ddl = """
    CREATE TABLE IF NOT EXISTS public.transactions (
        transaction_id    BIGSERIAL PRIMARY KEY,
        status            VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled'))
    );
    """

    parser = PostgreSQLParser()
    tables = parser.parse_ddl(postgres_ddl)

    assert len(tables) == 1
    table = tables[0]
    assert len(table.columns) == 2

    # Find status column
    status_col = table.get_column("status")
    assert status_col is not None
    assert status_col.default == "'pending'"
    assert status_col.data_type == "string"

    print("✅ Edge case tests passed!")


if __name__ == "__main__":
    test_transactions_table_parsing()
    test_transactions_table_conversion()
    test_specific_column_presence()
    test_edge_cases()
    print("🎉 All transactions table tests completed successfully!")
