"""Utility functions for pg2ch"""

import re
from typing import List, Optional


def clean_identifier(identifier: str) -> str:
    """Clean and normalize database identifiers"""
    # Remove quotes
    identifier = identifier.strip('"').strip("'").strip("`")

    # Handle schema.table format
    if "." in identifier:
        parts = identifier.split(".")
        return parts[-1]  # Return table name only

    return identifier


def normalize_type_name(type_name: str) -> str:
    """Normalize PostgreSQL type names"""
    # Remove precision/scale info for normalization
    base_type = re.sub(r"\([^)]*\)", "", type_name).strip().lower()

    # Handle common aliases
    aliases = {
        "int4": "integer",
        "int8": "bigint",
        "int2": "smallint",
        "float8": "double precision",
        "float4": "real",
        "bool": "boolean",
        "varchar": "character varying",
    }

    return aliases.get(base_type, base_type)


def extract_precision_scale(type_def: str) -> tuple[Optional[int], Optional[int]]:
    """Extract precision and scale from type definition like DECIMAL(10,2)"""
    match = re.search(r"\((\d+)(?:,\s*(\d+))?\)", type_def)
    if match:
        precision = int(match.group(1))
        scale = int(match.group(2)) if match.group(2) else None
        return precision, scale
    return None, None
