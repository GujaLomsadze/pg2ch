import json
from typing import List, Optional

from pydantic import BaseModel


class Column(BaseModel):
    """Represents a database column"""

    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False
    unique: bool = False
    comment: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name} {self.data_type}"

    def __repr__(self) -> str:
        """Detailed representation"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "default": self.default,
            "comment": self.comment,
        }
