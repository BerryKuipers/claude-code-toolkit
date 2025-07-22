# Crypto Portfolio Dashboard Deployment Script for Windows
# This script sets up the application for production deployment on Windows

param(
    [switch]$SkipTests,
    [switch]$Force
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Crypto Portfolio Dashboard Deployment..." -ForegroundColor Blue

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

try {
    # Check if Python is installed
    Write-Status "Checking Python installation..."
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python is not installed or not in PATH. Please install Python 3.8 or higher."
        exit 1
    }
    
    # Extract version number
    $versionMatch = [regex]::Match($pythonVersion, "Python (\d+\.\d+)")
    if ($versionMatch.Success) {
        $version = [version]$versionMatch.Groups[1].Value
        $requiredVersion = [version]"3.8"
        
        if ($version -lt $requiredVersion) {
            Write-Error "Python $($version.ToString()) is installed, but Python 3.8 or higher is required."
            exit 1
        }
        Write-Success "Python $($version.ToString()) detected"
    }

    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        Write-Status "Creating virtual environment..."
        python -m venv .venv
        Write-Success "Virtual environment created"
    } else {
        Write-Status "Virtual environment already exists"
    }

    # Activate virtual environment
    Write-Status "Activating virtual environment..."
    & ".\.venv\Scripts\Activate.ps1"

    # Upgrade pip
    Write-Status "Upgrading pip..."
    python -m pip install --upgrade pip

    # Install dependencies
    Write-Status "Installing dependencies..."
    pip install -r requirements.txt

    # Install the package in development mode
    Write-Status "Installing package in development mode..."
    pip install -e .

    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        if (Test-Path ".env.example") {
            Write-Status "Creating .env from .env.example..."
            Copy-Item ".env.example" ".env"
            Write-Warning "Please edit .env file with your Bitvavo API credentials"
        } else {
            Write-Status "Creating .env template..."
            @"
# Bitvavo API Configuration
BITVAVO_API_KEY=your_api_key_here
BITVAVO_API_SECRET=your_api_secret_here

# Dashboard Configuration
STREAMLIT_PORT=8503
LOG_LEVEL=INFO

# Optional: Override default settings
# CACHE_TIMEOUT=300
# MAX_RETRIES=3
"@ | Out-File -FilePath ".env" -Encoding UTF8
            Write-Warning "Please edit .env file with your Bitvavo API credentials"
        }
    } else {
        Write-Success ".env file already exists"
    }

    # Create logs directory
    if (-not (Test-Path "logs")) {
        Write-Status "Creating logs directory..."
        New-Item -ItemType Directory -Path "logs" | Out-Null
        Write-Success "Logs directory created"
    }

    # Run tests (unless skipped)
    if (-not $SkipTests) {
        Write-Status "Running tests..."
        try {
            python -m pytest tests/ -v
            Write-Success "All tests passed"
        } catch {
            Write-Warning "Some tests failed. Check the output above."
        }
    } else {
        Write-Status "Skipping tests as requested"
    }

    # Check if API credentials are configured
    Write-Status "Checking API configuration..."
    try {
        $apiCheck = python -c @"
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('BITVAVO_API_KEY')
api_secret = os.getenv('BITVAVO_API_SECRET')
if not api_key or api_key == 'your_api_key_here':
    print('API_KEY_MISSING')
elif not api_secret or api_secret == 'your_api_secret_here':
    print('API_SECRET_MISSING')
else:
    print('API_CONFIGURED')
"@
        
        if ($apiCheck -eq "API_CONFIGURED") {
            Write-Success "API credentials are configured"
        } else {
            Write-Warning "API credentials need to be configured in .env file"
        }
    } catch {
        Write-Warning "Could not check API configuration"
    }

    Write-Success "Deployment completed successfully!"
    Write-Host ""
    Write-Host "🎉 Next steps:" -ForegroundColor Green
    Write-Host "1. Edit .env file with your Bitvavo API credentials (if not done already)"
    Write-Host "2. Run the dashboard: python -m streamlit run dashboard.py --server.port 8503"
    Write-Host "3. Or use the CLI: python -m portfolio.cli --help"
    Write-Host ""
    Write-Host "📚 Documentation:" -ForegroundColor Blue
    Write-Host "- README.md: Complete setup and usage guide"
    Write-Host "- CONTRIBUTING.md: Development guidelines"
    Write-Host "- Dashboard URL: http://localhost:8503"
    Write-Host ""
    Write-Success "Happy trading! 📈"

} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}
