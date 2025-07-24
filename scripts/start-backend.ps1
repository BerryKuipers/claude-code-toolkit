# PowerShell script to start the FastAPI backend with type checking
# This script provides C#-like development experience with hot reload and type safety

param(
    [switch]$Production,
    [switch]$TypeCheck,
    [string]$Host = "0.0.0.0",
    [int]$Port = 8000
)

Write-Host "🚀 Starting Crypto Portfolio API Backend..." -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "backend/app/main.py")) {
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

# Check if backend dependencies are installed
Write-Host "📦 Checking backend dependencies..." -ForegroundColor Yellow
$backendRequirements = "backend/requirements.txt"
if (Test-Path $backendRequirements) {
    pip install -r $backendRequirements
} else {
    Write-Host "❌ Error: Backend requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Type checking (optional but recommended for C# developers)
if ($TypeCheck) {
    Write-Host "🔍 Running type checking with mypy..." -ForegroundColor Yellow
    mypy backend/app --strict --ignore-missing-imports
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Type checking found issues. Continue anyway? (y/n)" -ForegroundColor Yellow
        $continue = Read-Host
        if ($continue -ne "y") {
            exit 1
        }
    } else {
        Write-Host "✅ Type checking passed!" -ForegroundColor Green
    }
}

# Check environment variables
Write-Host "🔐 Checking environment variables..." -ForegroundColor Yellow
if (-not $env:BITVAVO_API_KEY) {
    Write-Host "❌ Error: BITVAVO_API_KEY environment variable not set" -ForegroundColor Red
    Write-Host "Please add it to your .env file or set it in your environment" -ForegroundColor Yellow
    exit 1
}

if (-not $env:BITVAVO_API_SECRET) {
    Write-Host "❌ Error: BITVAVO_API_SECRET environment variable not set" -ForegroundColor Red
    Write-Host "Please add it to your .env file or set it in your environment" -ForegroundColor Yellow
    exit 1
}

# Set working directory to backend
Set-Location backend

# Start the FastAPI server
Write-Host "🌐 Starting FastAPI server on http://$Host`:$Port" -ForegroundColor Green
Write-Host "📚 API Documentation will be available at:" -ForegroundColor Cyan
Write-Host "   - Swagger UI: http://$Host`:$Port/docs" -ForegroundColor Cyan
Write-Host "   - ReDoc: http://$Host`:$Port/redoc" -ForegroundColor Cyan
Write-Host "   - OpenAPI JSON: http://$Host`:$Port/openapi.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Hot reload enabled - changes will automatically restart the server" -ForegroundColor Green
Write-Host "🛑 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

if ($Production) {
    # Production mode - no reload, optimized settings
    uvicorn app.main:app --host $Host --port $Port --no-reload --workers 4
} else {
    # Development mode - with reload and debug
    uvicorn app.main:app --host $Host --port $Port --reload --log-level info
}
