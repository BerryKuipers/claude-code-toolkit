#!/bin/bash

# Crypto Portfolio Dashboard Deployment Script
# This script sets up the application for production deployment

set -e  # Exit on any error

echo "🚀 Starting Crypto Portfolio Dashboard Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
print_status "Installing package in development mode..."
pip install -e .

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    if [ -f ".env.example" ]; then
        print_status "Creating .env from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your Bitvavo API credentials"
    else
        print_status "Creating .env template..."
        cat > .env << EOF
# Bitvavo API Configuration
BITVAVO_API_KEY=your_api_key_here
BITVAVO_API_SECRET=your_api_secret_here

# Dashboard Configuration
STREAMLIT_PORT=8503
LOG_LEVEL=INFO

# Optional: Override default settings
# CACHE_TIMEOUT=300
# MAX_RETRIES=3
EOF
        print_warning "Please edit .env file with your Bitvavo API credentials"
    fi
else
    print_success ".env file already exists"
fi

# Create logs directory
if [ ! -d "logs" ]; then
    print_status "Creating logs directory..."
    mkdir -p logs
    print_success "Logs directory created"
fi

# Run tests
print_status "Running tests..."
if python -m pytest tests/ -v; then
    print_success "All tests passed"
else
    print_warning "Some tests failed. Check the output above."
fi

# Check if API credentials are configured
print_status "Checking API configuration..."
if python -c "
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
" 2>/dev/null; then
    API_STATUS=$(python -c "
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
")
    
    if [ "$API_STATUS" = "API_CONFIGURED" ]; then
        print_success "API credentials are configured"
    else
        print_warning "API credentials need to be configured in .env file"
    fi
else
    print_warning "Could not check API configuration"
fi

print_success "Deployment completed successfully!"
echo ""
echo "🎉 Next steps:"
echo "1. Edit .env file with your Bitvavo API credentials (if not done already)"
echo "2. Run the dashboard: python -m streamlit run dashboard.py --server.port 8503"
echo "3. Or use the CLI: python -m portfolio.cli --help"
echo ""
echo "📚 Documentation:"
echo "- README.md: Complete setup and usage guide"
echo "- CONTRIBUTING.md: Development guidelines"
echo "- Dashboard URL: http://localhost:8503"
echo ""
print_success "Happy trading! 📈"
