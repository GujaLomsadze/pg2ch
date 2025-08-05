# Dockerfile
FROM python:3.11-slim

# Set maintainer and labels
LABEL maintainer="your-email@example.com"
LABEL description="pg2ch - PostgreSQL to ClickHouse DDL Converter Web Interface"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Optional: Install ClickHouse Local for DDL validation
# Uncomment the next 3 lines if you want validation features
# RUN curl https://clickhouse.com/ | sh
# RUN chmod +x ./clickhouse
# RUN mv ./clickhouse /usr/local/bin/clickhouse-local

# Copy requirements first for better Docker layer caching
COPY web-ui/requirements-web.txt requirements-web.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-web.txt

# Copy pg2ch source code
#COPY src/ ./src/
#RUN #pip install --no-cache-dir -e ./src/

# Copy web application
COPY web-ui/ ./

# Create necessary directories and set permissions
RUN mkdir -p /app/static/uploads && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5003/api/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "2", "--timeout", "60", "app:app"]
