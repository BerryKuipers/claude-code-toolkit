# PowerShell script to start both backend and frontend services
# This provides the complete development environment with both services running

param(
    [switch]$TypeCheck,
    [switch]$Production,
    [string]$BackendHost = "localhost",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "localhost",
    [int]$FrontendPort = 8501
)

# Load Windows Forms for screen dimensions
Add-Type -AssemblyName System.Windows.Forms

# Add Windows API functions for window positioning
try {
    # Check if WindowManager type already exists
    if (-not ([System.Management.Automation.PSTypeName]'WindowManager').Type) {
        Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

public class WindowManager {
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern int GetSystemMetrics(int nIndex);

    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    public static void PositionWindow(IntPtr handle, int x, int y, int width, int height) {
        const uint SWP_NOZORDER = 0x0004;
        const uint SWP_SHOWWINDOW = 0x0040;
        SetWindowPos(handle, IntPtr.Zero, x, y, width, height, SWP_NOZORDER | SWP_SHOWWINDOW);
    }

    public static int GetScreenWidth() {
        return GetSystemMetrics(0); // SM_CXSCREEN
    }

    public static int GetScreenHeight() {
        return GetSystemMetrics(1); // SM_CYSCREEN
    }
}
"@
    }
} catch {
    Write-Host "⚠️  Window positioning API not available - windows will open in default positions" -ForegroundColor Yellow
}

function Get-ScreenDimensions {
    try {
        return @{
            Width = [WindowManager]::GetScreenWidth()
            Height = [WindowManager]::GetScreenHeight()
        }
    } catch {
        # Fallback to reasonable defaults
        return @{
            Width = 1920
            Height = 1080
        }
    }
}

function Set-WindowPosition {
    param(
        [System.Diagnostics.Process]$Process,
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$Height
    )

    # Wait for the window to be created
    $timeout = 10
    $elapsed = 0
    while ($Process.MainWindowHandle -eq [IntPtr]::Zero -and $elapsed -lt $timeout) {
        Start-Sleep -Milliseconds 500
        $Process.Refresh()
        $elapsed += 0.5
    }

    try {
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) {
            [WindowManager]::PositionWindow($Process.MainWindowHandle, $X, $Y, $Width, $Height)
            Write-Host "✅ Positioned window: $($Process.ProcessName) at ($X, $Y) size ($Width x $Height)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not get window handle for $($Process.ProcessName)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Window positioning failed for $($Process.ProcessName) - using default position" -ForegroundColor Yellow
    }
}



Write-Host "Starting Complete Crypto Portfolio Development Environment..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

# Kill any existing processes first
Write-Host "🧹 Cleaning up existing processes..." -ForegroundColor Yellow

# Kill all processes using ports 8000 and 8001 (backend)
Write-Host "   Checking for processes on ports 8000-8001..." -ForegroundColor Gray
$portsToCheck = @(8000, 8001)
foreach ($port in $portsToCheck) {
    try {
        $connections = netstat -ano | Select-String ":$port "
        if ($connections) {
            Write-Host "   Found processes on port $port, terminating..." -ForegroundColor Yellow
            $connections | ForEach-Object {
                $line = $_.Line.Trim()
                $parts = $line -split '\s+'
                if ($parts.Length -ge 5) {
                    $processId = $parts[-1]
                    if ($processId -match '^\d+$') {
                        try {
                            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                            Write-Host "     Killed PID $processId" -ForegroundColor Gray
                        } catch {
                            Write-Host "     Could not kill PID $processId" -ForegroundColor Yellow
                        }
                    }
                }
            }
        }
    } catch {
        Write-Host "   Error checking port $port" -ForegroundColor Yellow
    }
}

# Kill all Python processes related to our project
Write-Host "   Checking for Python processes..." -ForegroundColor Gray
try {
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*crypto_insight*" -or
        $_.CommandLine -like "*uvicorn*" -or
        $_.CommandLine -like "*streamlit*" -or
        $_.CommandLine -like "*app.main*" -or
        $_.CommandLine -like "*dashboard.py*"
    }

    if ($pythonProcesses) {
        Write-Host "   Found $($pythonProcesses.Count) Python processes to terminate..." -ForegroundColor Yellow
        $pythonProcesses | ForEach-Object {
            try {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                Write-Host "     Killed Python PID $($_.Id)" -ForegroundColor Gray
            } catch {
                Write-Host "     Could not kill Python PID $($_.Id)" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "   Error checking Python processes" -ForegroundColor Yellow
}

Write-Host "   Waiting for processes to terminate..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Verify ports are clear
Write-Host "   Verifying ports are clear..." -ForegroundColor Gray
foreach ($port in $portsToCheck) {
    $stillUsed = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
    if ($stillUsed) {
        Write-Host "   ⚠️  Port $port still in use after cleanup" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ Port $port is clear" -ForegroundColor Green
    }
}

Write-Host "✅ Process cleanup completed" -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "backend/app/main.py") -or -not (Test-Path "dashboard.py")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Function to start backend in background
function Start-Backend {
    Write-Host "Starting Backend API Server..." -ForegroundColor Yellow

    $backendArgs = @(
        "-NoExit",
        "-Command",
        "Set-Location '$PWD'; & '.\scripts\start-backend.ps1' -ServerHost '$BackendHost' -Port $BackendPort"
    )

    if ($TypeCheck) {
        $backendArgs[-1] += " -TypeCheck"
    }

    if ($Production) {
        $backendArgs[-1] += " -Production"
    }

    # Start backend in new window
    $backendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $backendArgs -PassThru -WindowStyle Normal

    # Position the backend window on the left side
    $screen = Get-ScreenDimensions
    $windowWidth = [int]($screen.Width / 2)
    $windowHeight = [int]($screen.Height * 0.8)
    Set-WindowPosition -Process $backendProcess -X 0 -Y 50 -Width $windowWidth -Height $windowHeight

    return $backendProcess
}

# Function to start frontend
function Start-Frontend {
    param($BackendUrl)

    Write-Host "Starting Frontend Dashboard..." -ForegroundColor Yellow

    # Wait a bit for backend to start
    Start-Sleep -Seconds 5

    $frontendArgs = @(
        "-NoExit",
        "-Command",
        "Set-Location '$PWD'; & '.\scripts\start-frontend.ps1' -ServerHost '$FrontendHost' -Port $FrontendPort -BackendUrl '$BackendUrl'"
    )

    # Start frontend in new window
    $frontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $frontendArgs -PassThru -WindowStyle Normal

    # Position the frontend window on the right side
    $screen = Get-ScreenDimensions
    $windowWidth = [int]($screen.Width / 2)
    $windowHeight = [int]($screen.Height * 0.8)
    Set-WindowPosition -Process $frontendProcess -X $windowWidth -Y 50 -Width $windowWidth -Height $windowHeight

    return $frontendProcess
}

# Start backend
$backendUrl = "http://$BackendHost`:$BackendPort"
# For frontend connection, use localhost instead of 0.0.0.0
$frontendBackendUrl = if ($BackendHost -eq "0.0.0.0") { "http://localhost:$BackendPort" } else { $backendUrl }

Write-Host "Backend will be available at: $backendUrl" -ForegroundColor Cyan
Write-Host "API Documentation at: $backendUrl/docs" -ForegroundColor Cyan

$backendProcess = Start-Backend

# Start frontend
$frontendUrl = "http://$FrontendHost`:$FrontendPort"
Write-Host "Frontend will be available at: $frontendUrl" -ForegroundColor Cyan
Write-Host "Frontend will connect to backend at: $frontendBackendUrl" -ForegroundColor Cyan

$frontendProcess = Start-Frontend -BackendUrl $frontendBackendUrl

Write-Host ""
Write-Host "Both services are starting up..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Services:" -ForegroundColor White
Write-Host "   Backend API:  $backendUrl" -ForegroundColor Cyan
Write-Host "   Frontend:     $frontendUrl" -ForegroundColor Cyan
Write-Host "   API Docs:     $backendUrl/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Development Features:" -ForegroundColor White
Write-Host "   Hot reload enabled for both services" -ForegroundColor Green
Write-Host "   Type safety with Pydantic models" -ForegroundColor Green
Write-Host "   Auto-generated API documentation" -ForegroundColor Green
Write-Host "   Independent service scaling" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan

# Wait for user to stop services
Write-Host ""
Write-Host "Both services are now running in separate windows!" -ForegroundColor Green
Write-Host "Backend (left window): $backendUrl" -ForegroundColor Cyan
Write-Host "Frontend (right window): $frontendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop both services, close this window or press Ctrl+C" -ForegroundColor Yellow
Write-Host "Individual services can be stopped by closing their respective windows" -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 5

        # Check if processes are still running
        if ($backendProcess.HasExited) {
            Write-Host "Backend process has stopped" -ForegroundColor Red
            break
        }

        if ($frontendProcess.HasExited) {
            Write-Host "Frontend process has stopped" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host "ERROR: An error occurred while running services" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Stopping services..." -ForegroundColor Yellow
} finally {
    # Clean up processes
    Write-Host "Cleaning up processes..." -ForegroundColor Yellow

    if ($backendProcess -and -not $backendProcess.HasExited) {
        Write-Host "Stopping backend..." -ForegroundColor Yellow
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }

    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Write-Host "Stopping frontend..." -ForegroundColor Yellow
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }

    Write-Host "All services stopped" -ForegroundColor Green
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
}
