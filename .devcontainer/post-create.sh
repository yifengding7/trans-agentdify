#!/bin/bash

# Post-create script for Video Subtitle Agent Dev Container
# This script runs after the container is created

set -e

echo "🚀 Setting up Video Subtitle Agent development environment..."

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

# Set up Git safe directory
print_status "Setting up Git configuration..."
git config --global --add safe.directory /workspace

# Install the project in development mode
print_status "Installing project in development mode..."
if [ -f "/workspace/pyproject.toml" ]; then
    cd /workspace
    pip install -e . --user
    print_success "Project installed in development mode"
else
    print_warning "pyproject.toml not found, skipping project installation"
fi

# Set up pre-commit hooks
print_status "Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    cd /workspace
    pre-commit install
    print_success "Pre-commit hooks installed"
else
    print_warning "pre-commit not found, skipping hook setup"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p /workspace/data/input
mkdir -p /workspace/data/output  
mkdir -p /workspace/data/temp
mkdir -p /workspace/logs
mkdir -p /workspace/models
mkdir -p /workspace/cache
print_success "Directories created"

# Set up environment variables file
print_status "Creating environment configuration..."
cat > /workspace/.env << 'EOF'
# Video Subtitle Agent Environment Configuration

# Development settings
DEVELOPMENT=true
LOG_LEVEL=DEBUG

# Model cache directories
TRANSFORMERS_CACHE=/home/vscode/.cache/huggingface
TORCH_HOME=/home/vscode/.cache/torch
TTS_CACHE_DIR=/home/vscode/.local/share/tts
SEAMLESS_CACHE_DIR=/home/vscode/.cache/seamless_communication

# Processing settings
MAX_WORKERS=2
BATCH_SIZE=1

# Hardware settings (for Apple Silicon in OrbStack)
PYTORCH_ENABLE_MPS_FALLBACK=1
CUDA_VISIBLE_DEVICES=""

# API settings (if using external services)
# OPENAI_API_KEY=your_key_here
# AZURE_OPENAI_API_KEY=your_key_here
EOF
print_success "Environment configuration created"

# Set up Jupyter Lab configuration
print_status "Setting up Jupyter Lab..."
mkdir -p /home/vscode/.jupyter
cat > /home/vscode/.jupyter/jupyter_lab_config.py << 'EOF'
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.token = ''
c.ServerApp.password = ''
c.ServerApp.allow_root = True
c.ServerApp.notebook_dir = '/workspace'
EOF
print_success "Jupyter Lab configured"

# Download and cache commonly used models (optional)
print_status "Checking model availability..."
python3 -c "
try:
    import torch
    print('✓ PyTorch available')
    
    # Check MPS availability
    if torch.backends.mps.is_available():
        print('✓ MPS (Apple Silicon acceleration) available')
    else:
        print('ℹ MPS not available (running on non-Apple Silicon or virtualized)')
        
except ImportError:
    print('⚠ PyTorch not available')

try:
    import transformers
    print('✓ Transformers available')
except ImportError:
    print('⚠ Transformers not available')
"

# Set up shell aliases and functions
print_status "Setting up shell aliases..."
cat >> /home/vscode/.bashrc << 'EOF'

# Video Subtitle Agent aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Project-specific aliases
alias vsa='cd /workspace'
alias run-tests='pytest tests/ -v'
alias format-code='black . && isort .'
alias lint-code='flake8 . && mypy .'
alias start-jupyter='jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline'

# Python aliases
alias py='python3'
alias pip='python3 -m pip'

# Show project status
function project-status() {
    echo "📁 Project: Video Subtitle Agent"
    echo "📍 Location: $(pwd)"
    echo "🐍 Python: $(python3 --version)"
    echo "📦 Git status:"
    git status --short
}

# Quick project commands
function quick-test() {
    echo "🧪 Running quick tests..."
    pytest tests/ -x -v --tb=short
}

function quick-format() {
    echo "🎨 Formatting code..."
    black . && isort .
    echo "✨ Code formatted!"
}

EOF

# Source the new aliases
source /home/vscode/.bashrc

print_success "Shell configuration updated"

# Display final status
echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  • vsa                 - Go to workspace"
echo "  • run-tests          - Run all tests"
echo "  • format-code        - Format code with black & isort"
echo "  • lint-code          - Lint code with flake8 & mypy"
echo "  • start-jupyter      - Start Jupyter Lab"
echo "  • project-status     - Show project info"
echo "  • quick-test         - Run quick tests"
echo "  • quick-format       - Quick code formatting"
echo ""
echo "🚀 Ready to start developing!"
echo "💡 Open Command Palette (Ctrl+Shift+P) and run 'Dev Containers: Reopen in Container'"
echo "" 