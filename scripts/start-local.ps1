# PowerShell script to start both backend and frontend services
# This provides the complete development environment with both services running

param(
    [switch]$TypeCheck,
    [switch]$Production,
    [string]$BackendHost = "0.0.0.0",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "localhost", 
    [int]$FrontendPort = 8501
)

Write-Host "🚀 Starting Complete Crypto Portfolio Development Environment..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

# Check if we're in the correct directory
if (-not (Test-Path "backend/app/main.py") -or -not (Test-Path "dashboard.py")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Function to start backend in background
function Start-Backend {
    Write-Host "🔧 Starting Backend API Server..." -ForegroundColor Yellow
    
    $backendArgs = @(
        "-File", "scripts\start-backend.ps1",
        "-Host", $BackendHost,
        "-Port", $BackendPort
    )
    
    if ($TypeCheck) {
        $backendArgs += "-TypeCheck"
    }
    
    if ($Production) {
        $backendArgs += "-Production"
    }
    
    $backendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $backendArgs -PassThru
    return $backendProcess
}

# Function to start frontend
function Start-Frontend {
    param($BackendUrl)
    
    Write-Host "🎨 Starting Frontend Dashboard..." -ForegroundColor Yellow
    
    # Wait a bit for backend to start
    Start-Sleep -Seconds 3
    
    $frontendArgs = @(
        "-File", "scripts\start-frontend.ps1",
        "-Host", $FrontendHost,
        "-Port", $FrontendPort,
        "-BackendUrl", $BackendUrl
    )
    
    $frontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $frontendArgs -PassThru
    return $frontendProcess
}

# Start backend
$backendUrl = "http://$BackendHost`:$BackendPort"
Write-Host "🌐 Backend will be available at: $backendUrl" -ForegroundColor Cyan
Write-Host "📚 API Documentation at: $backendUrl/docs" -ForegroundColor Cyan

$backendProcess = Start-Backend

# Start frontend
$frontendUrl = "http://$FrontendHost`:$FrontendPort"
Write-Host "🎨 Frontend will be available at: $frontendUrl" -ForegroundColor Cyan

$frontendProcess = Start-Frontend -BackendUrl $backendUrl

Write-Host ""
Write-Host "✅ Both services are starting up..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🔗 Services:" -ForegroundColor White
Write-Host "   Backend API:  $backendUrl" -ForegroundColor Cyan
Write-Host "   Frontend:     $frontendUrl" -ForegroundColor Cyan
Write-Host "   API Docs:     $backendUrl/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Development Features:" -ForegroundColor White
Write-Host "   ✅ Hot reload enabled for both services" -ForegroundColor Green
Write-Host "   ✅ Type safety with Pydantic models" -ForegroundColor Green
Write-Host "   ✅ Auto-generated API documentation" -ForegroundColor Green
Write-Host "   ✅ Independent service scaling" -ForegroundColor Green
Write-Host ""
Write-Host "🛑 Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan

# Wait for user to stop services
try {
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if processes are still running
        if ($backendProcess.HasExited) {
            Write-Host "❌ Backend process has stopped" -ForegroundColor Red
            break
        }
        
        if ($frontendProcess.HasExited) {
            Write-Host "❌ Frontend process has stopped" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
} finally {
    # Clean up processes
    if (-not $backendProcess.HasExited) {
        Write-Host "🔧 Stopping backend..." -ForegroundColor Yellow
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if (-not $frontendProcess.HasExited) {
        Write-Host "🎨 Stopping frontend..." -ForegroundColor Yellow
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "✅ All services stopped" -ForegroundColor Green
}
