"""
pg2ch - PostgreSQL to ClickHouse DDL Converter
"""

__version__ = "0.1.0"

from .converters.clickhouse_converter import ClickHouseConverter
from .main import convert_ddl, convert_file
from .parsers.postgres_parser import PostgreSQLParser
from .validators.validate_ch_ddl import validate_clickhouse_ddl_with_local

__all__ = [
    "convert_ddl",
    "PostgreSQLParser",
    "ClickHouseConverter",
    "validate_clickhouse_ddl_with_local",
]
