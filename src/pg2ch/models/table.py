import json
from typing import List, Optional

from pydantic import BaseModel

from .column import Column


class Table(BaseModel):
    """Represents a database table"""

    name: str
    schema_name: str = "public"
    columns: List[Column] = []
    primary_keys: List[str] = []
    indexes: List[str] = []
    comment: Optional[str] = None

    def add_column(self, column: Column) -> None:
        """Add a column to the table"""
        self.columns.append(column)

    def get_column(self, name: str) -> Optional[Column]:
        """Get a column by name"""
        for column in self.columns:
            if column.name == name:
                return column
        return None

    def __str__(self) -> str:
        """Beautiful formatted string representation"""
        lines = []
        lines.append(f"Table: {self.name}")
        lines.append(f"   Schema: {self.schema_name}")
        lines.append(f"   Columns: {len(self.columns)}")

        if self.primary_keys:
            lines.append(f"   Primary Keys: {', '.join(self.primary_keys)}")

        lines.append(f"   Column Details:")
        for i, col in enumerate(self.columns, 1):
            constraints = []
            if col.primary_key:
                constraints.append("PK")
            if col.unique:
                constraints.append("UNIQUE")
            if not col.nullable:
                constraints.append("NOT NULL")
            if col.default:
                constraints.append(f"DEFAULT {col.default}")

            constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
            lines.append(f"      {i:2d}. {col.name} → {col.data_type}{constraint_str}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "schema": self.schema_name,
            "total_columns": len(self.columns),
            "primary_keys": self.primary_keys,
            "indexes": self.indexes,
            "comment": self.comment,
            "columns": [col.to_dict() for col in self.columns],
        }

    def to_json(self, indent: int = 2) -> str:
        """Get JSON representation as string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def print_json(self, indent: int = 2) -> None:
        """Print table metadata as formatted JSON"""
        print(self.to_json(indent=indent))
