# Scripts Directory

This directory contains utility scripts for development, deployment, and GitHub workflow automation.

## 🚀 Quick Setup

Run the setup script to install all required tools:

```bash
./scripts/setup-dev-environment.sh
```

This installs:
- PowerShell 7.4+ for cross-platform scripting
- GitHub CLI for GitHub API access
- Python development tools (black, isort, pytest, etc.)
- Node.js tools (if npm is available)

## 📋 Available Scripts

### Development Environment
- **`setup-dev-environment.sh`** - One-time setup of development tools

### GitHub Workflow Automation
- **`resolve-pr-conversations.ps1`** - PowerShell script to resolve PR conversations (requires GitHub CLI)
- **`resolve-pr-conversations.sh`** - Bash script to resolve PR conversations (requires GitHub CLI + jq)
- **`resolve-pr-conversations.py`** - Python script to resolve PR conversations (requires GITHUB_TOKEN env var)

### CI/CD
- **`run-ci-checks.ps1`** - PowerShell CI checks
- **`run-ci-checks.sh`** - Bash CI checks
- **`deploy.ps1`** - PowerShell deployment script
- **`deploy.sh`** - Bash deployment script

## 🔐 Authentication Setup

### For Augment Environments
Since Augment workspaces may not persist authentication, the Python script is recommended as it uses environment variables:

```bash
# Use the Python script with environment token
python scripts/resolve-pr-conversations.py -o BerryKuipers -r crypto-insight -p 33 -d
```

### For Local Development
Set up GitHub CLI authentication for full functionality:

```bash
gh auth login
```

## 🛠️ Usage Examples

### Resolve PR Conversations

**Dry run (preview only):**
```bash
# Python (recommended for Augment)
python scripts/resolve-pr-conversations.py -o BerryKuipers -r crypto-insight -p 33 -d

# PowerShell (requires gh auth)
pwsh scripts/resolve-pr-conversations.ps1 -Owner "BerryKuipers" -Repo "crypto-insight" -PrNumber 33 -DryRun

# Bash (requires gh auth)
./scripts/resolve-pr-conversations.sh -o BerryKuipers -r crypto-insight -p 33 -d
```

**Actually resolve conversations:**
```bash
# Remove the -d flag to actually resolve
python scripts/resolve-pr-conversations.py -o BerryKuipers -r crypto-insight -p 33
```

### CI Checks

#### `run-ci-checks.ps1` (PowerShell - Windows)
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
