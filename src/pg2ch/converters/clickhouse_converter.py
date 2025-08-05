from typing import List

from ..models.column import Column
from ..models.table import Table
from ..validators.validate_ch_ddl import validate_clickhouse_ddl_with_local


class ClickHouseConverter:
    """Converter for ClickHouse DDL generation"""

    # Generic to ClickHouse type mapping
    TYPE_MAPPING = {
        "string": "String",
        "integer": "Int32",
        "bigint": "Int64",
        "smallint": "Int16",
        "boolean": "Bool",
        "decimal": "Decimal64(4)",
        "float": "Float32",
        "double": "Float64",
        "datetime": "DateTime",
        "date": "Date",
        "time": "String",  # ClickHouse doesn't have native time type
    }

    def __init__(self):
        pass

    def convert_tables(self, tables: List[Table]) -> str:
        """
        Convert a list of tables to ClickHouse DDL

        Args:
            tables: List of Table objects

        Returns:
            ClickHouse DDL as string
        """
        ddl_statements = []

        for table in tables:
            ddl = self.convert_table(table)
            ddl_statements.append(ddl)

        return "\n\n".join(ddl_statements)

    def convert_table(self, table: Table) -> str:
        """
        Convert a single table to ClickHouse DDL

        Args:
            table: Table object

        Returns:
            ClickHouse CREATE TABLE statement
        """
        lines = []
        lines.append(f"CREATE TABLE {table.name} (")

        # Add columns
        column_definitions = []
        for column in table.columns:
            col_def = self._convert_column(column)
            column_definitions.append(f"    {col_def}")

        lines.append(",\n".join(column_definitions))
        lines.append(")")

        # Add ENGINE (using MergeTree as default)
        engine_clause = self._generate_engine_clause(table)
        lines.append(f"ENGINE = {engine_clause}")

        # Add ORDER BY clause if there are primary keys
        if table.primary_keys:
            order_by = ", ".join(table.primary_keys)
            lines.append(f"ORDER BY ({order_by})")

        lines.append(";")

        return "\n".join(lines)

    def _convert_column(self, column: Column) -> str:
        """Convert a single column to ClickHouse format"""
        # Map data type
        ch_type = self.TYPE_MAPPING.get(column.data_type, column.data_type)

        # Handle nullable types
        if column.nullable and not column.primary_key:
            ch_type = f"Nullable({ch_type})"

        column_def = f"{column.name} {ch_type}"

        # Add default value if specified
        if column.default:
            # Clean up default value
            default_val = column.default
            if default_val.lower() == "null":
                default_val = "NULL"
            elif default_val.startswith("'") and default_val.endswith("'"):
                # Keep string defaults as-is
                pass
            else:
                # For other defaults, might need conversion
                pass

            column_def += f" DEFAULT {default_val}"

        # Add comment if available
        if column.comment:
            column_def += f" COMMENT '{column.comment}'"

        return column_def

    def _generate_engine_clause(self, table: Table) -> str:
        """Generate appropriate ENGINE clause for ClickHouse"""
        # Use MergeTree family as default
        # You can enhance this logic based on table characteristics
        return "MergeTree()"
