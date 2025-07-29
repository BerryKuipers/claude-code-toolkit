# PowerShell script to start the FastAPI backend with type checking
# This script provides C#-like development experience with hot reload and type safety

param(
    [switch]$Production,
    [switch]$TypeCheck,
    [string]$ServerHost = "0.0.0.0",
    [int]$Port = 8000
)

Write-Host "Starting Crypto Portfolio API Backend..." -ForegroundColor Green

# Kill any existing backend processes
Write-Host "Checking for existing backend processes..." -ForegroundColor Yellow
$existingProcesses = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*uvicorn*" }
if ($existingProcesses) {
    Write-Host "Found existing backend processes. Stopping them..." -ForegroundColor Yellow
    $existingProcesses | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

# Check if we're in the correct directory
if (-not (Test-Path "backend/app/main.py")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv/Scripts/Activate.ps1") {
    & .venv/Scripts/Activate.ps1
} else {
    Write-Host "Error: Virtual environment not found. Please run setup first." -ForegroundColor Red
    exit 1
}

# Check if backend dependencies are installed
Write-Host "Checking backend dependencies..." -ForegroundColor Yellow
$backendRequirements = "backend/requirements.txt"
if (Test-Path $backendRequirements) {
    pip install -r $backendRequirements
} else {
    Write-Host "Error: Backend requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Type checking (optional but recommended for C# developers)
if ($TypeCheck) {
    Write-Host "Running type checking with mypy..." -ForegroundColor Yellow
    mypy backend/app --strict --ignore-missing-imports
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Type checking found issues. Continue anyway? (y/n)" -ForegroundColor Yellow
        $continue = Read-Host
        if ($continue -ne "y") {
            exit 1
        }
    } else {
        Write-Host "Type checking passed!" -ForegroundColor Green
    }
}

# Check if .env file exists (Python app will load environment variables from here)
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Please create a .env file with your API keys" -ForegroundColor Yellow
    Write-Host "The application may fail to start without proper configuration" -ForegroundColor Yellow
} else {
    Write-Host "Configuration file (.env) found" -ForegroundColor Green
}

# Test Python imports before starting server
Write-Host "Testing Python imports..." -ForegroundColor Yellow

# Set working directory to backend first
Set-Location backend

# Simple test - just try to import the main app module
Write-Host "Testing FastAPI app import..." -ForegroundColor Yellow
python -c "from app.main import app; print('SUCCESS: FastAPI app import successful')"
$appImportResult = $LASTEXITCODE

if ($appImportResult -ne 0) {
    Write-Host "FastAPI app import failed - cannot start server" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "1. Check if all dependencies are installed" -ForegroundColor Yellow
    Write-Host "2. Verify the src directory exists in project root" -ForegroundColor Yellow
    Write-Host "3. Make sure you're running from the correct directory" -ForegroundColor Yellow
    Write-Host "4. Ensure virtual environment is activated" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Import test passed - ready to start server" -ForegroundColor Green

# Start the FastAPI server
Write-Host "Starting FastAPI server on http://$ServerHost`:$Port" -ForegroundColor Green
Write-Host "API Documentation will be available at:" -ForegroundColor Cyan
Write-Host "   - Swagger UI: http://$ServerHost`:$Port/docs" -ForegroundColor Cyan
Write-Host "   - ReDoc: http://$ServerHost`:$Port/redoc" -ForegroundColor Cyan
Write-Host "   - OpenAPI JSON: http://$ServerHost`:$Port/openapi.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "Hot reload enabled - changes will automatically restart the server" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

Write-Host "Starting uvicorn server..." -ForegroundColor Green

try {
    if ($Production) {
        # Production mode - no reload, optimized settings
        Write-Host "Running in PRODUCTION mode" -ForegroundColor Yellow
        uvicorn app.main:app --host $ServerHost --port $Port --no-reload --workers 4
    } else {
        # Development mode - with reload and debug
        Write-Host "Running in DEVELOPMENT mode" -ForegroundColor Green
        uvicorn app.main:app --host $ServerHost --port $Port --reload --log-level info
    }
} catch {
    Write-Host "ERROR: Failed to start uvicorn server" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Full error: $($_.Exception)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Check if port $Port is already in use" -ForegroundColor Yellow
    Write-Host "2. Verify .env file contains required API keys" -ForegroundColor Yellow
    Write-Host "3. Check Python import paths and dependencies" -ForegroundColor Yellow
    Write-Host "4. Review the error log above for specific issues" -ForegroundColor Yellow

    # Keep the window open so user can see the error
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
