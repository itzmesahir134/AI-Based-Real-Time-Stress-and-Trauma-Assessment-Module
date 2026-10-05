# SaathiAI — One-Click Hackathon Demo Launcher (PowerShell)
# Starts FastAPI backend, seeds sample data, and starts Next.js frontend

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      🚀 Starting SaathiAI Live Demo Environment          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Train ML models & seed database
Write-Host "`n[1/3] Training ML checkpoints & seeding demo database..." -ForegroundColor Yellow
python scripts/train_models.py
python scripts/seed_demo_data.py

# 2. Start FastAPI Backend in background
Write-Host "`n[2/3] Starting FastAPI backend server on port 8000..." -ForegroundColor Yellow
$BackendProcess = Start-Process python -ArgumentList "-m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru

# 3. Start Next.js Frontend
Write-Host "`n[3/3] Starting Next.js frontend on port 3000..." -ForegroundColor Yellow
Write-Host "🌐 Opening UI at http://localhost:3000/login in your browser..." -ForegroundColor Green

Start-Process "http://localhost:3000/login"

cd apps/web
npm run dev

# Cleanup on exit
Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
