# tests/test_customers_table.py
"""
Test for customers table parsing to ensure correct metadata extraction
"""

import pytest

from pg2ch import PostgreSQLParser


def test_customers_table_parsing():
    """Test that customers table is parsed correctly and matches expected JSON structure"""

    # PostgreSQL DDL
    postgres_ddl = """
    CREATE TABLE customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        age INTEGER,
        balance DECIMAL(10,2) DEFAULT 0.00,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP
    );
    """

    # Expected result
    expected_table_dict = {
        "name": "customers",
        "schema": "public",
        "total_columns": 8,
        "primary_keys": ["id"],
        "indexes": [],
        "comment": None,
        "columns": [
            {
                "name": "id",
                "data_type": "integer",
                "nullable": True,
                "primary_key": True,
                "unique": False,
                "default": None,
                "comment": None,
            },
            {
                "name": "name",
                "data_type": "string",
                "nullable": False,
                "primary_key": False,
                "unique": False,
                "default": None,
                "comment": None,
            },
            {
                "name": "email",
                "data_type": "string",
                "nullable": True,
                "primary_key": False,
                "unique": True,
                "default": None,
                "comment": None,
            },
            {
                "name": "age",
                "data_type": "integer",
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "comment": None,
            },
            {
                "name": "balance",
                "data_type": "decimal",
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": "0.00",
                "comment": None,
            },
            {
                "name": "is_active",
                "data_type": "boolean",
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": "true",
                "comment": None,
            },
            {
                "name": "created_at",
                "data_type": "datetime",
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": "NOW()",
                "comment": None,
            },
            {
                "name": "updated_at",
                "data_type": "datetime",
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "comment": None,
            },
        ],
    }

    # Parse the DDL
    parser = PostgreSQLParser()
    tables = parser.parse_ddl(postgres_ddl)

    # Assertions
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"

    table = tables[0]
    actual_table_dict = table.to_dict()

    # Test table-level properties
    assert actual_table_dict["name"] == expected_table_dict["name"]
    assert actual_table_dict["schema"] == expected_table_dict["schema"]
    assert actual_table_dict["total_columns"] == expected_table_dict["total_columns"]
    assert actual_table_dict["primary_keys"] == expected_table_dict["primary_keys"]
    assert actual_table_dict["indexes"] == expected_table_dict["indexes"]
    assert actual_table_dict["comment"] == expected_table_dict["comment"]

    # Test columns
    assert len(actual_table_dict["columns"]) == len(expected_table_dict["columns"])

    for i, (actual_col, expected_col) in enumerate(
        zip(actual_table_dict["columns"], expected_table_dict["columns"])
    ):
        assert (
            actual_col == expected_col
        ), f"Column {i} mismatch:\nActual: {actual_col}\nExpected: {expected_col}"

    # Test the complete dictionary
    assert (
        actual_table_dict == expected_table_dict
    ), "Complete table dictionary does not match expected result"

    print("✅ All assertions passed! Table parsing is working correctly.")


def test_individual_column_properties():
    """Test individual column properties separately for easier debugging"""

    postgres_ddl = """
    CREATE TABLE customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        age INTEGER,
        balance DECIMAL(10,2) DEFAULT 0.00,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP
    );
    """

    parser = PostgreSQLParser()
    tables = parser.parse_ddl(postgres_ddl)
    table = tables[0]

    # Test specific columns
    id_col = table.get_column("id")
    assert id_col is not None
    assert id_col.data_type == "integer"
    assert id_col.primary_key == True
    assert (
        id_col.nullable == True
    )  # Note: SERIAL columns are technically nullable in our mapping

    name_col = table.get_column("name")
    assert name_col is not None
    assert name_col.data_type == "string"
    assert name_col.nullable == False
    assert name_col.primary_key == False

    email_col = table.get_column("email")
    assert email_col is not None
    assert email_col.unique == True

    balance_col = table.get_column("balance")
    assert balance_col is not None
    assert balance_col.default == "0.00"

    print("✅ Individual column property tests passed!")


if __name__ == "__main__":
    test_customers_table_parsing()
    test_individual_column_properties()
    print("🎉 All tests completed successfully!")
