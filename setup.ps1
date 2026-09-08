# SIH26189 — AI-Powered Criminal Network Analysis System
# PowerShell Setup and Seeding Script for Windows Host

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🛡️  SIH26189 — Starting Environment Orchestration 🛡️" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Clean previous runs
Write-Host "🧹 Stopping existing containers and cleaning volumes..." -ForegroundColor Yellow
docker compose down -v --remove-orphans

# 2. Build containers
Write-Host "🏗️ Building backend and frontend Docker containers..." -ForegroundColor Yellow
docker compose build

# 3. Bring up database
Write-Host "🗄️ Starting PostgreSQL database service..." -ForegroundColor Yellow
docker compose up -d db

# 4. Wait for Postgres to be ready
Write-Host "⏳ Waiting for database connection validation..." -ForegroundColor Yellow
while ($true) {
    $ready = docker compose exec db pg_isready -U postgres -d criminal_network
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Write-Host "   Database is starting up... waiting 2 seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}
Write-Host "✅ Database connection established." -ForegroundColor Green

# 5. Run synthetic data generator
Write-Host "🌱 Running synthetic data generator and seeding tables..." -ForegroundColor Yellow
docker compose run --rm backend python ml/generate_data.py

# 6. Run ML training pipeline
Write-Host "🧠 Training models (Risk classification, Link prediction, Anomaly forest)..." -ForegroundColor Yellow
docker compose run --rm backend python ml/train.py

# 7. Run automated tests to verify build integrity
Write-Host "🧪 Running automated backend test suite..." -ForegroundColor Yellow
docker compose run --rm backend pytest

# 8. Start full system
Write-Host "🚀 Booting backend API and React frontend..." -ForegroundColor Yellow
docker compose up -d backend frontend

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "✨ SYSTEM BOOTED SUCCESSFULLY! ✨" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "🛡️ Web Application UI:  http://localhost:8080" -ForegroundColor Cyan
Write-Host "🔌 FastAPI Server API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "🔌 API Docs Swagger:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Run 'docker compose logs -f' to follow log updates." -ForegroundColor Gray
