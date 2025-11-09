#!/bin/bash
# Finance Tracker - Local Development Startup Script
# This script starts the Flask application with sensible defaults for local development

set -e

echo "=========================================="
echo "Finance Tracker - Local Development"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Set development environment variables (only if not already set)
export FLASK_ENV="${FLASK_ENV:-development}"
export FLASK_PORT="${FLASK_PORT:-5001}"

# Check if SECRET_KEY is set, if not use development default
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  SECRET_KEY not set - using development default"
    export SECRET_KEY="dev-secret-key-change-in-production"
fi

echo "✅ Configuration:"
echo "   FLASK_ENV: $FLASK_ENV"
echo "   FLASK_PORT: $FLASK_PORT"
echo "   SECRET_KEY: ${SECRET_KEY:0:20}..."

# Check if database exists
if [ ! -f "data/finance.db" ]; then
    echo "⚠️  Database not found - initializing..."
    mkdir -p data
fi

echo ""
echo "🚀 Starting Flask server..."
echo "   Application: http://localhost:$FLASK_PORT"
echo "   Dashboard:   http://localhost:$FLASK_PORT/dashboard"
echo "   Deals:       http://localhost:$FLASK_PORT/deals"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask
python run.py
