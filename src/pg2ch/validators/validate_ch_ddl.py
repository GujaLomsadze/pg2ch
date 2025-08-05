import os
import subprocess
import tempfile
from typing import Tuple


def validate_clickhouse_ddl_with_local(ddl: str) -> Tuple[bool, str]:
    """
    Validate ClickHouse DDL using clickhouse-local via stdin
    """
    try:
        # Run clickhouse-local with DDL via stdin
        result = subprocess.run(
            [
                "clickhouse-local",
                "--query",
                ddl,
            ],
            input=ddl,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            return True, "----------- ✅ DDL is valid"
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return False, f"❌ DDL validation failed: {error_msg}"

    except FileNotFoundError:
        return False, "❌ clickhouse-local not found. Install ClickHouse Locally please"
    except subprocess.TimeoutExpired:
        return False, "❌ Validation timeout"
    except Exception as e:
        return False, f"❌ Validation error: {str(e)}"
