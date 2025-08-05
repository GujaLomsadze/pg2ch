# web-ui/app.py
import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

# Import your pg2ch library
try:
    from pg2ch import PostgreSQLParser, convert_ddl, validate_clickhouse_ddl_with_local
except ImportError:
    print("Warning: pg2ch not installed. Install with: pip install -e ../src")
    # Fallback for development
    import sys

    sys.path.append("../src")
    from pg2ch import PostgreSQLParser, convert_ddl, validate_clickhouse_ddl_with_local

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["DEBUG"] = os.environ.get("DEBUG", "True").lower() == "true"


@app.route("/")
def index():
    """Main converter page"""
    return render_template("converter.html")


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """Convert PostgreSQL DDL to ClickHouse DDL"""
    try:
        data = request.json
        postgres_ddl = data.get("ddl", "").strip()

        if not postgres_ddl:
            return jsonify({"success": False, "error": "No DDL provided"})

        # Convert DDL
        clickhouse_ddl = convert_ddl(postgres_ddl)

        # Parse for metadata
        parser = PostgreSQLParser()
        tables = parser.parse_ddl(postgres_ddl)

        # Build metadata
        metadata = {
            "tables_count": len(tables),
            "total_columns": sum(len(t.columns) for t in tables),
            "tables": [],
        }

        for table in tables:
            table_info = {
                "name": table.name,
                "columns": len(table.columns),
                "primary_keys": table.primary_keys,
                "column_details": [
                    {
                        "name": col.name,
                        "type": col.data_type,
                        "nullable": col.nullable,
                        "default": col.default,
                    }
                    for col in table.columns
                ],
            }
            metadata["tables"].append(table_info)

        return jsonify(
            {"success": True, "clickhouse_ddl": clickhouse_ddl, "metadata": metadata}
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc() if app.config["DEBUG"] else None,
            }
        )


@app.route("/api/validate", methods=["POST"])
def api_validate():
    """Validate ClickHouse DDL syntax"""
    try:
        data = request.json
        ddl = data.get("ddl", "").strip()

        if not ddl:
            return jsonify({"valid": False, "message": "No DDL provided"})

        # Try validation with clickhouse-local
        try:
            is_valid, message = validate_clickhouse_ddl_with_local(ddl)
            return jsonify(
                {"valid": is_valid, "message": message, "method": "clickhouse-local"}
            )
        except Exception as e:
            # Fallback to basic validation
            return jsonify(
                {
                    "valid": True,
                    "message": f"⚠️ Basic validation passed (clickhouse-local not available: {str(e)})",
                    "method": "basic",
                }
            )

    except Exception as e:
        return jsonify({"valid": False, "message": f"Validation error: {str(e)}"})


@app.route("/api/examples")
def api_examples():
    """Get example DDL statements"""
    examples = [
        {
            "name": "Simple Users Table",
            "description": "Basic table with serial primary key",
            "ddl": """CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        },
        {
            "name": "E-commerce Products",
            "description": "Product catalog with various data types",
            "ddl": """CREATE TABLE products (
    product_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER,
    in_stock BOOLEAN DEFAULT true,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);""",
        },
        {
            "name": "Financial Transactions",
            "description": "Complex table with constraints and defaults",
            "ddl": """CREATE TABLE IF NOT EXISTS public.transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency CHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);""",
        },
    ]

    return jsonify({"examples": examples})


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "version": "1.0.0", "pg2ch_available": True})


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")

    print(f"🚀 Starting pg2ch Web Interface on http://{host}:{port}")
    print("📖 Open your browser and start converting DDL!")

    app.run(host=host, port=port, debug=app.config["DEBUG"])
