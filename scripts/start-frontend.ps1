# PowerShell script to start the Streamlit frontend
# This script starts the frontend that communicates with the typed API backend

param(
    [string]$Host = "localhost",
    [int]$Port = 8501,
    [string]$BackendUrl = "http://localhost:8000"
)

Write-Host "🎨 Starting Crypto Portfolio Frontend..." -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "dashboard.py")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv/Scripts/Activate.ps1") {
    & .venv/Scripts/Activate.ps1
} else {
    Write-Host "❌ Error: Virtual environment not found. Please run setup first." -ForegroundColor Red
    exit 1
}

# Check if frontend dependencies are installed
Write-Host "📦 Checking frontend dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Set backend URL environment variable for the frontend
$env:BACKEND_API_URL = $BackendUrl

# Check if backend is running
Write-Host "🔍 Checking if backend is running at $BackendUrl..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is running and healthy!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Backend responded but may not be healthy" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Warning: Backend not responding at $BackendUrl" -ForegroundColor Red
    Write-Host "   Make sure to start the backend first with: .\scripts\start-backend.ps1" -ForegroundColor Yellow
    Write-Host "   Continuing anyway - frontend will show connection errors..." -ForegroundColor Yellow
}

# Start Streamlit
Write-Host "🌐 Starting Streamlit frontend on http://$Host`:$Port" -ForegroundColor Green
Write-Host "🔗 Frontend will connect to backend at: $BackendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Hot reload enabled - changes will automatically refresh" -ForegroundColor Green
Write-Host "🛑 Press Ctrl+C to stop the frontend" -ForegroundColor Yellow
Write-Host ""

streamlit run dashboard.py --server.address $Host --server.port $Port --server.headless false
