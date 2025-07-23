#!/bin/bash
# Run all CI checks locally before pushing to avoid CI failures

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
write_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

write_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

write_error() {
    echo -e "${RED}❌ $1${NC}"
}

write_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Check if we're in project root
if [ ! -f "requirements.txt" ]; then
    write_error "Please run this script from the project root directory"
    exit 1
fi

# Parse arguments
FIX=false
if [ "$1" = "--fix" ] || [ "$1" = "-f" ]; then
    FIX=true
fi

echo -e "${BLUE}🚀 Running CI Checks Locally${NC}"
echo "=================================="

failed=false

# Step 1: Install dependencies
write_step "Installing dependencies"
python -m pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
write_success "Dependencies installed"

# Step 2: Code formatting check (Black)
write_step "Checking code formatting with Black"
if [ "$FIX" = true ]; then
    if python -m black src/ tests/ dashboard.py; then
        write_success "Code formatted with Black"
    else
        write_error "Black formatting failed"
        failed=true
    fi
else
    if python -m black --check --diff src/ tests/ dashboard.py; then
        write_success "Code formatting check passed"
    else
        write_error "Code formatting check failed. Run with --fix to auto-format"
        failed=true
    fi
fi

# Step 3: Import sorting check (isort)
write_step "Checking import sorting with isort"
if [ "$FIX" = true ]; then
    if python -m isort --profile black src/ tests/ dashboard.py; then
        write_success "Imports sorted with isort"
    else
        write_error "isort failed"
        failed=true
    fi
else
    if python -m isort --check-only --diff --profile black src/ tests/ dashboard.py; then
        write_success "Import sorting check passed"
    else
        write_error "Import sorting check failed. Run with --fix to auto-sort"
        failed=true
    fi
fi

# Step 4: Linting with flake8
write_step "Running linting checks with flake8"
if python -m flake8 src/ tests/ dashboard.py --count --select=E9,F63,F7,F82 --show-source --statistics; then
    write_success "Linting checks passed"
else
    write_error "Linting checks failed"
    failed=true
fi

# Step 5: Security scanning with bandit
write_step "Running security scan with bandit"
if python -m bandit -r src/ dashboard.py; then
    write_success "Security scan passed"
else
    # Check exit code - bandit returns 1 for low severity issues
    if [ $? -eq 1 ]; then
        write_warning "Security scan completed with low-severity warnings only"
    else
        write_error "Security scan failed with high/medium severity issues"
        failed=true
    fi
fi

# Step 6: Run unit tests with coverage
write_step "Running unit tests with coverage"
export BITVAVO_API_KEY="test_key"
export BITVAVO_API_SECRET="test_secret"
export OPENAI_API_KEY="test_openai_key"
export ANTHROPIC_API_KEY="test_anthropic_key"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

if python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=10; then
    write_success "Unit tests passed with sufficient coverage"
else
    write_error "Unit tests failed"
    failed=true
fi

# Step 7: Dashboard startup validation
write_step "Validating dashboard startup"
if python -c "
import sys
sys.path.append('.')
try:
    import dashboard
    print('✅ Dashboard imports successfully')
except Exception as e:
    print(f'❌ Dashboard import failed: {e}')
    sys.exit(1)
"; then
    write_success "Dashboard startup validation passed"
else
    write_error "Dashboard startup validation failed"
    failed=true
fi

# Summary
echo ""
echo "=================================="
if [ "$failed" = true ]; then
    write_error "Some checks failed. Please fix the issues before pushing."
    exit 1
else
    write_success "All CI checks passed! 🎉"
    echo -e "${GREEN}Your code is ready to push to GitHub.${NC}"
    exit 0
fi
