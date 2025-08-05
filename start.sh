#!/bin/bash
echo "🚀 Starting pg2ch PostgreSQL to ClickHouse Converter..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create uploads directory
mkdir -p uploads

# Start the application
echo "📦 Building and starting containers..."
docker compose up -d

# Wait a moment for startup
sleep 3

# Check if it's running
if docker compose ps | grep -q "Up"; then
    echo "✅ pg2ch is now running!"
    echo "🌐 Open your browser and go to: http://localhost:5000"
    echo ""
    echo "📋 Useful commands:"
    echo "   docker compose logs -f    # View logs"
    echo "   docker compose down       # Stop the application"
    echo "   docker compose restart    # Restart the application"
else
    echo "❌ Failed to start. Check logs with: docker compose logs"
fi
