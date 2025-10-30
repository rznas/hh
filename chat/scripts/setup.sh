#!/bin/bash
# Setup script for ocular triage chat system

set -e

echo "🚀 Setting up Ocular Triage Chat System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "🐍 Creating virtual environment with uv..."
    uv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -r requirements-dev.txt

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running. Please start Docker to use database services."
else
    echo "🐳 Starting database services..."
    docker-compose up -d postgres neo4j redis

    echo "⏳ Waiting for databases to be ready..."
    sleep 10
fi

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Edit .env file with your API keys"
echo "  2. Run: chainlit run src/app.py"
echo "  3. Or with Docker: docker-compose up"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
