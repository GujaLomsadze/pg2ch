"""Custom exceptions for pg2ch"""


class Pg2chError(Exception):
    """Base exception for pg2ch"""

    pass


class ParseError(Pg2chError):
    """Raised when DDL parsing fails"""

    pass


class ConversionError(Pg2chError):
    """Raised when DDL conversion fails"""

    pass
