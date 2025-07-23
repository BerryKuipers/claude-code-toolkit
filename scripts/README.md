# CI Check Scripts

This directory contains scripts to run all CI checks locally before pushing to GitHub, preventing CI failures and saving time.

## Scripts

### `run-ci-checks.ps1` (PowerShell - Windows)
```powershell
# Run all checks (read-only)
.\scripts\run-ci-checks.ps1

# Run all checks and auto-fix formatting issues
.\scripts\run-ci-checks.ps1 -Fix
```

### `run-ci-checks.sh` (Bash - Cross-platform)
```bash
# Run all checks (read-only)
./scripts/run-ci-checks.sh

# Run all checks and auto-fix formatting issues  
./scripts/run-ci-checks.sh --fix
```

## What Gets Checked

The scripts run the exact same checks as GitHub Actions CI:

1. **Dependencies**: Install/update all required packages
2. **Code Formatting**: Black formatter compliance
3. **Import Sorting**: isort compliance  
4. **Linting**: flake8 syntax and style checks
5. **Security Scanning**: bandit security vulnerability scan
6. **Unit Tests**: pytest with coverage reporting
7. **Dashboard Validation**: Ensure dashboard imports successfully

## Usage Workflow

**Before every push:**
```powershell
# 1. Run checks to see what needs fixing
.\scripts\run-ci-checks.ps1

# 2. If formatting issues found, auto-fix them
.\scripts\run-ci-checks.ps1 -Fix

# 3. Commit and push (CI should now pass)
git add .
git commit -m "Your commit message"
git push
```

## Benefits

- ✅ **Catch issues early** - Fix problems locally instead of in CI
- ⚡ **Save time** - No more back-and-forth with failed CI runs
- 🔧 **Auto-fix** - Automatically resolve formatting and import issues
- 🎯 **Exact match** - Same checks as GitHub Actions CI
- 📊 **Clear output** - Color-coded results with helpful error messages

## Requirements

- Python virtual environment activated (`.venv`)
- All dependencies installed (`pip install -r requirements.txt`)
- PowerShell 5.1+ (for .ps1 script) or Bash (for .sh script)

## Troubleshooting

**Virtual environment not detected:**
```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1
```

**Permission errors on Windows:**
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Script not found:**
```bash
# Make bash script executable
chmod +x scripts/run-ci-checks.sh
```
