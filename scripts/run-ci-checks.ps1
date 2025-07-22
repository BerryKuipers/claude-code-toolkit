#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run all CI checks locally before pushing to avoid CI failures
    
.DESCRIPTION
    This script runs the exact same checks that GitHub Actions CI runs:
    - Code formatting (Black)
    - Import sorting (isort) 
    - Linting (flake8)
    - Security scanning (bandit)
    - Unit tests with coverage
    - Dashboard startup validation
    
.PARAMETER Fix
    Automatically fix formatting and import issues
    
.EXAMPLE
    .\scripts\run-ci-checks.ps1
    .\scripts\run-ci-checks.ps1 -Fix
#>

param(
    [switch]$Fix
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-Step {
    param($Message)
    Write-Host "${Blue}🔄 $Message${Reset}"
}

function Write-Success {
    param($Message)
    Write-Host "${Green}✅ $Message${Reset}"
}

function Write-Error {
    param($Message)
    Write-Host "${Red}❌ $Message${Reset}"
}

function Write-Warning {
    param($Message)
    Write-Host "${Yellow}⚠️ $Message${Reset}"
}

# Ensure we're in the project root
if (-not (Test-Path "requirements.txt")) {
    Write-Error "Please run this script from the project root directory"
    exit 1
}

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Warning "Virtual environment not detected. Activating .venv..."
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .\.venv\Scripts\Activate.ps1
    } else {
        Write-Error "Virtual environment not found. Please create one with: python -m venv .venv"
        exit 1
    }
}

Write-Host "${Blue}🚀 Running CI Checks Locally${Reset}"
Write-Host "=================================="

$failed = $false

# Step 1: Install dependencies
Write-Step "Installing dependencies"
try {
    python -m pip install --upgrade pip | Out-Null
    pip install -r requirements.txt | Out-Null
    Write-Success "Dependencies installed"
} catch {
    Write-Error "Failed to install dependencies: $_"
    $failed = $true
}

# Step 2: Code formatting check (Black)
Write-Step "Checking code formatting with Black"
if ($Fix) {
    $blackResult = python -m black src/ tests/ dashboard.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Code formatted with Black"
    } else {
        Write-Error "Black formatting failed: $blackResult"
        $failed = $true
    }
} else {
    $blackResult = python -m black --check --diff src/ tests/ dashboard.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Code formatting check passed"
    } else {
        Write-Error "Code formatting check failed. Run with -Fix to auto-format"
        Write-Host $blackResult
        $failed = $true
    }
}

# Step 3: Import sorting check (isort)
Write-Step "Checking import sorting with isort"
if ($Fix) {
    $isortResult = python -m isort src/ tests/ dashboard.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Imports sorted with isort"
    } else {
        Write-Error "isort failed: $isortResult"
        $failed = $true
    }
} else {
    $isortResult = python -m isort --check-only --diff src/ tests/ dashboard.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Import sorting check passed"
    } else {
        Write-Error "Import sorting check failed. Run with -Fix to auto-sort"
        Write-Host $isortResult
        $failed = $true
    }
}

# Step 4: Linting with flake8
Write-Step "Running linting checks with flake8"
$flakeResult = python -m flake8 src/ tests/ dashboard.py --count --select=E9,F63,F7,F82 --show-source --statistics 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Linting checks passed"
} else {
    Write-Error "Linting checks failed:"
    Write-Host $flakeResult
    $failed = $true
}

# Step 5: Security scanning with bandit
Write-Step "Running security scan with bandit"
$banditResult = python -m bandit -r src/ dashboard.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Security scan passed"
} else {
    # Check if it's just warnings or actual failures
    if ($banditResult -match "Total issues.*High: 0.*Medium: 0") {
        Write-Warning "Security scan completed with low-severity warnings only"
    } else {
        Write-Error "Security scan failed:"
        Write-Host $banditResult
        $failed = $true
    }
}

# Step 6: Run unit tests with coverage
Write-Step "Running unit tests with coverage"
$env:BITVAVO_API_KEY = "test_key"
$env:BITVAVO_API_SECRET = "test_secret"
$env:OPENAI_API_KEY = "test_openai_key"
$env:ANTHROPIC_API_KEY = "test_anthropic_key"

$testResult = python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=5 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Unit tests passed with sufficient coverage"
} else {
    Write-Error "Unit tests failed:"
    Write-Host $testResult
    $failed = $true
}

# Step 7: Dashboard startup validation
Write-Step "Validating dashboard startup"
$dashboardTest = python -c "
import sys
sys.path.append('.')
try:
    import dashboard
    print('✅ Dashboard imports successfully')
except Exception as e:
    print(f'❌ Dashboard import failed: {e}')
    sys.exit(1)
" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Dashboard startup validation passed"
} else {
    Write-Error "Dashboard startup validation failed:"
    Write-Host $dashboardTest
    $failed = $true
}

# Summary
Write-Host ""
Write-Host "=================================="
if ($failed) {
    Write-Error "Some checks failed. Please fix the issues before pushing."
    exit 1
} else {
    Write-Success "All CI checks passed! 🎉"
    Write-Host "${Green}Your code is ready to push to GitHub.${Reset}"
    exit 0
}
