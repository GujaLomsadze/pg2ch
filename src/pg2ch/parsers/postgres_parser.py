import re
from typing import Any, Dict, List, Optional

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, Name

from ..models.column import Column
from ..models.table import Table
from ..utils.exceptions import ParseError


class TableList(list):
    """Enhanced list for Table objects with beautiful printing"""

    def __str__(self) -> str:
        """Beautiful formatted representation of all tables"""
        # ... beautiful formatting logic ...

    def __repr__(self) -> str:
        """JSON representation of all tables"""
        # ... JSON formatting logic ...

    def print_json(self) -> None:
        """Print all metadata as formatted JSON"""

    def print_summary(self) -> None:
        """Print a summary of all tables"""


class PostgreSQLParser:
    """Parser for PostgreSQL DDL statements"""

    # PostgreSQL to generic type mapping
    TYPE_MAPPING = {
        "serial": "integer",
        "bigserial": "bigint",
        "smallserial": "smallint",
        "varchar": "string",
        "text": "string",
        "char": "string",
        "character": "string",
        "character varying": "string",
        "boolean": "boolean",
        "bool": "boolean",
        "smallint": "smallint",
        "integer": "integer",
        "int": "integer",
        "int4": "integer",
        "bigint": "bigint",
        "int8": "bigint",
        "decimal": "decimal",
        "numeric": "decimal",
        "real": "float",
        "double precision": "double",
        "float8": "double",
        "timestamp": "datetime",
        "timestamp with time zone": "datetime",
        "timestamp without time zone": "datetime",
        "timestamptz": "datetime",
        "date": "date",
        "time": "time",
        "json": "string",
        "jsonb": "string",
        "uuid": "string",
    }

    def __init__(self):
        pass

    def parse_ddl(self, ddl_text: str) -> List[Table]:
        """
        Parse PostgreSQL DDL and return a list of Table objects

        Args:
            ddl_text: PostgreSQL DDL statements as string

        Returns:
            List of Table objects

        Raises:
            ParseError: If parsing fails
        """
        try:
            statements = sqlparse.parse(ddl_text)
            tables = []

            for statement in statements:
                if self._is_create_table_statement(statement):
                    table = self._parse_create_table(statement)
                    if table:
                        tables.append(table)

            return tables

        except Exception as e:
            raise ParseError(f"Failed to parse DDL: {str(e)}")

    def _is_create_table_statement(self, statement: Statement) -> bool:
        """Check if statement is a CREATE TABLE statement"""
        tokens = [token for token in statement.flatten() if not token.is_whitespace]

        if len(tokens) < 3:
            return False

        return (
            tokens[0].value.upper() == "CREATE"
            and tokens[1].ttype is Keyword
            and tokens[1].value.upper() == "TABLE"
        )

    def _parse_create_table(self, statement: Statement) -> Optional[Table]:
        """Parse a CREATE TABLE statement"""
        try:
            # Extract table name
            table_name = self._extract_table_name(statement)
            if not table_name:
                return None

            # Extract columns
            columns = self._extract_columns(statement)

            # Create table object
            table = Table(name=table_name, columns=columns)

            # Extract primary keys
            primary_keys = self._extract_primary_keys(statement)
            table.primary_keys = primary_keys

            return table

        except Exception as e:
            print(f"Warning: Failed to parse table: {str(e)}")
            return None

    def _extract_table_name(self, statement: Statement) -> Optional[str]:
        """Extract table name from CREATE TABLE statement"""
        tokens = [token for token in statement.flatten() if not token.is_whitespace]

        # Find TABLE keyword and get the table identifier
        table_keyword_index = None
        for i, token in enumerate(tokens):
            if token.ttype is Keyword and token.value.upper() == "TABLE":
                table_keyword_index = i
                break

        if table_keyword_index is None:
            return None

        # Look for table name after TABLE keyword
        search_start = table_keyword_index + 1

        # Skip IF NOT EXISTS if present
        if (
            search_start < len(tokens) - 2
            and tokens[search_start].value.upper() == "IF"
            and search_start + 1 < len(tokens)
            and tokens[search_start + 1].value.upper() == "NOT"
            and search_start + 2 < len(tokens)
            and tokens[search_start + 2].value.upper() == "EXISTS"
        ):
            search_start += 3

        # Get the table name - handle schema.table when tokens are separate
        if search_start < len(tokens):
            # Check if we have schema.table pattern (separate tokens)
            if (
                search_start + 2 < len(tokens)
                and tokens[search_start + 1].value == "."
                and tokens[search_start + 2].ttype is not None
            ):
                # We have schema.table as separate tokens: schema, ., table
                table_name = tokens[search_start + 2].value
            else:
                # Single token (might contain schema.table or just table)
                table_identifier = tokens[search_start].value
                if "." in table_identifier:
                    table_name = table_identifier.split(".")[-1]
                else:
                    table_name = table_identifier

            # Remove quotes
            table_name = table_name.strip('"').strip("'")
            return table_name

        return None

    def _extract_columns(self, statement: Statement) -> List[Column]:
        """Extract column definitions from CREATE TABLE statement"""
        columns = []

        # Find the parentheses containing column definitions
        sql_text = str(statement)

        # Simple regex to find column definitions (basic implementation)
        # This is a simplified parser - you might want to enhance this for production
        column_pattern = r"(\w+)\s+([\w\s\(\),]+?)(?:,|\s*\)|\s*$)"

        # Extract content between first ( and last )
        paren_start = sql_text.find("(")
        paren_end = sql_text.rfind(")")

        if paren_start == -1 or paren_end == -1:
            return columns

        column_section = sql_text[paren_start + 1 : paren_end]

        # Split by comma but be careful of function calls
        column_defs = self._split_column_definitions(column_section)

        for col_def in column_defs:
            column = self._parse_column_definition(col_def.strip())
            if column:
                columns.append(column)

        return columns

    def _split_column_definitions(self, text: str) -> List[str]:
        """Split column definitions by comma, handling nested parentheses"""
        parts = []
        current = ""
        paren_count = 0

        for char in text:
            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
            elif char == "," and paren_count == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                continue

            current += char

        if current.strip():
            parts.append(current.strip())

        return parts

    def _parse_column_definition(self, col_def: str) -> Optional[Column]:
        """Parse a single column definition"""
        if not col_def.strip():
            return None

        # Clean up the definition
        col_def = col_def.strip().rstrip(",")
        col_def_upper = col_def.upper()

        # Skip ONLY table-level constraints that don't represent columns
        if any(
            col_def_upper.startswith(keyword)
            for keyword in ["PRIMARY KEY (", "FOREIGN KEY (", "UNIQUE (", "CONSTRAINT "]
        ):
            return None

        # Split by whitespace but be careful with parentheses
        parts = []
        current_part = ""
        paren_count = 0

        for char in col_def:
            if char == "(":
                paren_count += 1
                current_part += char
            elif char == ")":
                paren_count -= 1
                current_part += char
            elif char.isspace() and paren_count == 0:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char

        if current_part:
            parts.append(current_part)

        if len(parts) < 2:
            return None

        name = parts[0].strip('"').strip("'")
        data_type = parts[1]

        # Handle type with precision/scale like VARCHAR(20)
        if "(" in data_type and ")" in data_type:
            base_type = data_type.split("(")[0]
        else:
            base_type = data_type

        # Handle special PostgreSQL types
        base_type_lower = base_type.lower()
        if base_type_lower in ["varchar", "character varying"]:
            base_type_lower = "varchar"
        elif "timestamp" in base_type_lower:
            base_type_lower = "timestamp"

        # Normalize type
        normalized_type = self.TYPE_MAPPING.get(base_type_lower, base_type_lower)

        # Check for constraints in the remaining parts
        remaining_text = " ".join(parts[2:]).upper()
        nullable = "NOT NULL" not in remaining_text
        primary_key = "PRIMARY KEY" in remaining_text
        unique = "UNIQUE" in remaining_text

        # Extract default value (look for DEFAULT keyword)
        default = None
        if "DEFAULT" in remaining_text:
            # Find DEFAULT and get the next token
            default_parts = col_def.split()
            for i, part in enumerate(default_parts):
                if part.upper() == "DEFAULT" and i + 1 < len(default_parts):
                    default_value = default_parts[i + 1]
                    # Handle quoted strings
                    if default_value.startswith("'") and default_value.endswith("'"):
                        default = default_value
                    else:
                        default = default_value
                    # Convert PostgreSQL defaults to ClickHouse
                    if default and default.upper() == "CURRENT_TIMESTAMP":
                        default = "NOW()"
                    break

        return Column(
            name=name,
            data_type=normalized_type,
            nullable=nullable,
            default=default,
            primary_key=primary_key,
            unique=unique,
        )

    def _extract_primary_keys(self, statement: Statement) -> List[str]:
        """Extract primary key column names"""
        sql_text = str(statement).upper()
        primary_keys = []

        # Method 1: Look for table-level PRIMARY KEY constraint: PRIMARY KEY (col1, col2)
        pk_constraint_match = re.search(r"PRIMARY KEY\s*\(([^)]+)\)", sql_text)
        if pk_constraint_match:
            pk_columns = [
                col.strip().strip('"').strip("'")
                for col in pk_constraint_match.group(1).split(",")
            ]
            primary_keys.extend(pk_columns)

        # Method 2: Look for inline PRIMARY KEY in column definitions
        # Handle both "column_name TYPE PRIMARY KEY" and multi-line format
        lines = sql_text.split("\n")
        current_column = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line starts a new column definition
            parts = line.split()
            if (
                len(parts) >= 2
                and not line.startswith("PRIMARY KEY")
                and not line.startswith("CONSTRAINT")
            ):
                # This looks like a column definition
                potential_column = parts[0].strip(",").strip('"').strip("'")
                if potential_column.lower() not in [
                    "primary",
                    "key",
                    "constraint",
                    "unique",
                    "check",
                    "foreign",
                ]:
                    current_column = potential_column.lower()

            # Check if PRIMARY KEY appears on this line (same line or following line)
            if "PRIMARY KEY" in line:
                if current_column and not line.startswith("PRIMARY KEY"):
                    # This is an inline or multi-line primary key for current_column
                    primary_keys.append(current_column)
                elif line.startswith("PRIMARY KEY") and current_column:
                    # This is a continuation line with PRIMARY KEY for the previous column
                    primary_keys.append(current_column)

        return list(set(primary_keys))  # Remove duplicates
