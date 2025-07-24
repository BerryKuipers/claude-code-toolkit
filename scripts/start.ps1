#!/usr/bin/env pwsh
# Start script for crypto-insight dashboard
# Activates virtual environment and runs Streamlit with auto-recompiling

Write-Host "🚀 Starting Crypto Insight Dashboard..." -ForegroundColor Green

# Change to project directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "📁 Project directory: $ProjectRoot" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "💡 Please run setup first or create virtual environment" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Check if Streamlit is installed
try {
    $streamlitVersion = & streamlit --version 2>$null
    Write-Host "✅ Streamlit found: $streamlitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Streamlit not found in virtual environment" -ForegroundColor Red
    Write-Host "💡 Please install dependencies: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Start Streamlit with auto-recompiling
Write-Host "🌐 Starting Streamlit dashboard with auto-recompiling..." -ForegroundColor Green
Write-Host "📱 Dashboard will be available at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "🔄 Auto-recompiling enabled - changes will be reflected automatically!" -ForegroundColor Yellow
Write-Host "⏹️  Press Ctrl+C to stop the server" -ForegroundColor Magenta

# Run Streamlit with proper error handling
try {
    streamlit run dashboard.py --server.runOnSave=true --server.fileWatcherType=auto
} catch {
    Write-Host "❌ Error starting Streamlit: $_" -ForegroundColor Red
    Write-Host "💡 Make sure all dependencies are installed and API keys are configured" -ForegroundColor Yellow
    exit 1
}
