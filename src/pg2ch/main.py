from pathlib import Path
from typing import Optional

import click

from .converters.clickhouse_converter import ClickHouseConverter
from .parsers.postgres_parser import PostgreSQLParser
from .utils.exceptions import ParseError
from .validators.validate_ch_ddl import validate_clickhouse_ddl_with_local


def convert_ddl(postgres_ddl: str, validate: bool = False) -> str:
    """
    Convert PostgreSQL DDL to ClickHouse DDL

    Args:
        postgres_ddl: PostgreSQL DDL statements as string
        validate: Boolean if it should be validated using `clickhouse-local` or not

    Returns:
        ClickHouse DDL as string

    Raises:
        ParseError: If parsing fails
    """
    parser = PostgreSQLParser()
    converter = ClickHouseConverter()

    # Parse PostgreSQL DDL
    tables = parser.parse_ddl(postgres_ddl)

    # Convert to ClickHouse DDL
    clickhouse_ddl = converter.convert_tables(tables)

    if validate:
        is_valid_ddl, message = validate_clickhouse_ddl_with_local(ddl=clickhouse_ddl)
        print(message)

    return clickhouse_ddl


def convert_file(
    input_file: str, output_file: Optional[str] = None, validate: bool = False
) -> str:
    """
    Convert PostgreSQL DDL file to ClickHouse DDL file

    Args:
        input_file: Path to PostgreSQL DDL file
        output_file: Path to output ClickHouse DDL file (optional)
        validate: Validate with clickhouse-local or not

    Returns:
        ClickHouse DDL as string
    """
    # Read input file
    with open(input_file, "r", encoding="utf-8") as f:
        postgres_ddl = f.read()

    # Convert DDL
    clickhouse_ddl = convert_ddl(postgres_ddl, validate=validate)

    # Write output file if specified
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(clickhouse_ddl)

    return clickhouse_ddl


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--validate", "-v", is_flag=True, help="Validate DDL using `clickhouse-local`"
)
def cli(input_file: str, output: Optional[str], validate: bool) -> None:
    """Convert PostgreSQL DDL to ClickHouse DDL"""
    try:
        result = convert_file(input_file, output, validate)

        if output:
            click.echo(f"Conversion complete! Output written to {output}")
        else:
            click.echo("Conversion complete!")
            click.echo("\n--- ClickHouse DDL ---")
            click.echo(result)

    except ParseError as e:
        click.echo(f"Parse error: {e}", err=True)
        exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        exit(1)


if __name__ == "__main__":
    cli()
