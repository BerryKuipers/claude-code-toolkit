#!/bin/bash
# Setup development environment with PowerShell and GitHub CLI

set -e

echo "🚀 Setting up development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_warning "This script is designed for Linux. Some steps may not work on other systems."
fi

# Install PowerShell
print_status "Installing PowerShell..."
if command -v pwsh &> /dev/null; then
    print_success "PowerShell is already installed: $(pwsh --version)"
else
    # Download and install PowerShell
    PWSH_VERSION="7.4.0"
    PWSH_URL="https://github.com/PowerShell/PowerShell/releases/download/v${PWSH_VERSION}/powershell-${PWSH_VERSION}-linux-x64.tar.gz"
    
    print_status "Downloading PowerShell ${PWSH_VERSION}..."
    curl -L "$PWSH_URL" -o /tmp/powershell.tar.gz
    
    print_status "Installing PowerShell to ~/.local/bin/powershell..."
    mkdir -p ~/.local/bin/powershell
    tar -xzf /tmp/powershell.tar.gz -C ~/.local/bin/powershell
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin/powershell:"* ]]; then
        echo 'export PATH="$HOME/.local/bin/powershell:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin/powershell:$PATH"
    fi
    
    # Create symlink for easier access
    sudo ln -sf ~/.local/bin/powershell/pwsh /usr/local/bin/pwsh 2>/dev/null || {
        print_warning "Could not create system-wide symlink. PowerShell available as ~/.local/bin/powershell/pwsh"
    }
    
    rm /tmp/powershell.tar.gz
    print_success "PowerShell installed: $(~/.local/bin/powershell/pwsh --version)"
fi

# Install GitHub CLI
print_status "Installing GitHub CLI..."
if command -v gh &> /dev/null; then
    print_success "GitHub CLI is already installed: $(gh --version | head -n1)"
else
    print_status "Adding GitHub CLI repository..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    
    print_status "Installing GitHub CLI..."
    sudo apt update && sudo apt install gh -y
    
    print_success "GitHub CLI installed: $(gh --version | head -n1)"
fi

# Install other useful development tools
print_status "Installing additional development tools..."

# Python tools
if command -v pip &> /dev/null; then
    print_status "Installing Python development tools..."
    pip install --user black isort pytest flake8 mypy
    print_success "Python tools installed"
else
    print_warning "pip not found, skipping Python tools"
fi

# Node.js tools (if Node.js is available)
if command -v npm &> /dev/null; then
    print_status "Installing Node.js development tools..."
    npm install -g prettier eslint
    print_success "Node.js tools installed"
else
    print_warning "npm not found, skipping Node.js tools"
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/*.sh scripts/*.ps1 2>/dev/null || true

print_success "Development environment setup complete!"
echo ""
echo "📋 Available tools:"
echo "  - PowerShell: pwsh or ~/.local/bin/powershell/pwsh"
echo "  - GitHub CLI: gh"
echo "  - Python tools: black, isort, pytest, flake8, mypy"
if command -v npm &> /dev/null; then
    echo "  - Node.js tools: prettier, eslint"
fi
echo ""
echo "🔧 Usage examples:"
echo "  - Resolve PR conversations (PowerShell): pwsh scripts/resolve-pr-conversations.ps1 -Owner 'BerryKuipers' -Repo 'crypto-insight' -PrNumber 33"
echo "  - Resolve PR conversations (Python): python scripts/resolve-pr-conversations.py -o BerryKuipers -r crypto-insight -p 33 -d"
echo "  - Resolve PR conversations (Bash): ./scripts/resolve-pr-conversations.sh -o BerryKuipers -r crypto-insight -p 33 -d"
echo "  - Run CI checks: ./scripts/run-ci-checks.sh"
echo "  - Format code: black . && isort --profile black src/ tests/"
echo ""
echo "🔐 GitHub Authentication:"
echo "  For GitHub CLI: gh auth login"
echo "  For Python script: Set GITHUB_TOKEN environment variable"
echo "  For PowerShell script: Requires GitHub CLI authentication"
echo ""
echo "💡 Tips:"
echo "  - Restart your terminal or run 'source ~/.bashrc' to ensure PATH is updated"
echo "  - Use dry-run mode (-d) to preview changes before applying them"
echo "  - The Python script works with environment variables and doesn't require GitHub CLI"
