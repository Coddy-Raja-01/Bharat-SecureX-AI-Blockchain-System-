#!/bin/bash
# SIH26189 — AI-Powered Criminal Network Analysis System
# Setup and Seeding Script

set -e

echo "=========================================================="
echo "🛡️  SIH26189 — Starting Environment Orchestration 🛡️"
echo "=========================================================="

# 1. Clean previous runs
echo "🧹 Stopping existing containers and cleaning volumes..."
docker compose down -v --remove-orphans

# 2. Build containers
echo "🏗️ Building backend and frontend Docker containers..."
docker compose build

# 3. Bring up database
echo "🗄️ Starting PostgreSQL database service..."
docker compose up -d db

# 4. Wait for Postgres to be ready
echo "⏳ Waiting for database connection validation..."
until docker compose exec db pg_isready -U postgres -d criminal_network >/dev/null 2>&1; do
    echo "   Database is starting up... waiting 2 seconds..."
    sleep 2
done
echo "✅ Database connection established."

# 5. Run synthetic data generator
echo "🌱 Running synthetic data generator and seeding tables..."
docker compose run --rm backend python ml/generate_data.py

# 6. Run ML training pipeline
echo "🧠 Training models (Risk classification, Link prediction, Anomaly forest)..."
docker compose run --rm backend python ml/train.py

# 7. Run automated tests to verify build integrity
echo "🧪 Running automated backend test suite..."
docker compose run --rm backend pytest

# 8. Start full system
echo "🚀 Booting backend API and React frontend..."
docker compose up -d backend frontend

echo ""
echo "=========================================================="
echo "✨ SYSTEM BOOTED SUCCESSFULLY! ✨"
echo "=========================================================="
echo "🛡️ Web Application UI:  http://localhost:8080"
echo "🔌 FastAPI Server API:  http://localhost:8000"
echo "🔌 API Docs Swagger:    http://localhost:8000/docs"
echo "=========================================================="
echo "Run 'docker compose logs -f' to follow log updates."
