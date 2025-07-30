# Installation Guide

Complete installation guide for The Alchemiser trading engine.

## System Requirements

### Operating System

- **macOS**: 10.15+ (Catalina or later)
- **Linux**: Ubuntu 20.04+, CentOS 8+, or equivalent
- **Windows**: Windows 10+ with WSL2 (Windows Subsystem for Linux)

### Python Requirements

- **Python**: 3.11 or higher (recommended: 3.11.7+)
- **pip**: Latest version (comes with Python)
- **virtualenv**: For isolated environments

### Hardware Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space for installation and data
- **Network**: Stable internet connection for API access

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone repository
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser

# Install with Make (handles everything)
make install
```

This will:
- Create virtual environment
- Install all dependencies
- Setup CLI commands
- Verify installation

### Method 2: Manual Installation

```bash
# Clone repository
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in development mode
pip install -e .

# Verify installation
alchemiser version
```

### Method 3: Docker Installation

```bash
# Build Docker image
docker build -t alchemiser .

# Run in container
docker run --env-file .env alchemiser version
```

## Dependency Installation

### Core Dependencies

The following packages are automatically installed:

```
# Trading and Data
alpaca-py>=0.42.0          # Alpaca Markets API
twelve-data>=1.2.9         # Market data provider
pandas>=2.1.0              # Data manipulation
numpy>=1.24.0              # Numerical computing

# CLI and UI
typer>=0.12.0              # CLI framework
rich>=13.7.0               # Rich terminal output
click>=8.1.0               # Command line interface

# Web and Networking
requests>=2.31.0           # HTTP requests
websockets>=12.0           # WebSocket connections
aiohttp>=3.9.0             # Async HTTP client

# Utilities
python-dotenv>=1.0.0       # Environment variables
pyyaml>=6.0                # YAML configuration
jinja2>=3.1.0              # Template engine

# Development (optional)
pytest>=7.4.0              # Testing framework
black>=23.0.0              # Code formatting
flake8>=6.0.0              # Code linting
```

### Optional Dependencies

For additional features:

```bash
# Enhanced email notifications
pip install pillow>=10.0.0  # Image processing for charts

# Performance monitoring
pip install psutil>=5.9.0   # System monitoring

# Advanced data analysis
pip install matplotlib>=3.7.0  # Plotting and charts
pip install seaborn>=0.12.0     # Statistical visualization

# Database storage (if needed)
pip install sqlalchemy>=2.0.0  # Database ORM
```

## API Account Setup

### Alpaca Markets Account

1. **Create Account**:
   - Visit [Alpaca Markets](https://alpaca.markets)
   - Sign up for a free account
   - Complete identity verification

2. **Get API Keys**:
   - Log into your Alpaca dashboard
   - Navigate to "API Keys" section
   - Generate **Paper Trading** keys first
   - Optionally generate **Live Trading** keys later

3. **API Key Permissions**:
   - Ensure keys have "Trading" permissions enabled
   - "Account" and "Data" permissions are also required

### TwelveData API (Optional)

For enhanced market data:

1. Visit [TwelveData](https://twelvedata.com)
2. Create free account (500 requests/day)
3. Get API key from dashboard
4. Add to environment variables

## Environment Configuration

### Create Environment File

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

### Environment Variables

```bash
# Required: Alpaca Paper Trading
ALPACA_KEY=your_paper_api_key_here
ALPACA_SECRET=your_paper_secret_here

# Optional: Alpaca Live Trading (use with caution)
ALPACA_LIVE_KEY=your_live_api_key_here
ALPACA_LIVE_SECRET=your_live_secret_here

# Optional: Enhanced Market Data
TWELVE_DATA_API_KEY=your_twelve_data_key_here

# Optional: Email Notifications
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECIPIENTS=recipient1@email.com,recipient2@email.com

# Optional: Configuration
LOG_LEVEL=INFO
CONFIG_FILE=config.yaml
```

### Email Setup (Gmail)

For Gmail email notifications:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL_PASSWORD`

## Verification

### Test Installation

```bash
# Check version and dependencies
alchemiser version --dependencies

# Test API connectivity
alchemiser status

# Generate test signals
alchemiser bot
```

### Expected Output

```
🔧 THE ALCHEMISER VERSION INFORMATION

Version: 2.1.0
Python: 3.11.7
Platform: macOS-14.2.1-arm64
Installation: Development (/path/to/alchemiser)

📦 KEY DEPENDENCIES
├── alpaca-py: 0.42.0 ✅
├── typer: 0.12.3 ✅
├── rich: 13.7.1 ✅
└── requests: 2.31.0 ✅

🌐 API CONNECTIVITY
├── ✅ Alpaca Paper API: Connected
└── ✅ Market Data: Available
```

## Platform-Specific Instructions

### macOS Setup

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Make sure Python 3.11 is in PATH
export PATH="/opt/homebrew/bin:$PATH"

# Verify Python version
python3 --version  # Should show 3.11.x

# Clone and install
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser
make install
```

### Ubuntu/Debian Setup

```bash
# Update package list
sudo apt update

# Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo apt install git curl build-essential

# Install pip
curl https://bootstrap.pypa.io/get-pip.py | python3.11

# Clone and install
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Windows (WSL2) Setup

```bash
# Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# Open Ubuntu terminal and update
sudo apt update && sudo apt upgrade

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo apt install git curl build-essential

# Clone and install
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### CentOS/RHEL Setup

```bash
# Enable EPEL repository
sudo dnf install epel-release

# Install Python 3.11
sudo dnf install python3.11 python3.11-devel python3.11-pip
sudo dnf install git curl gcc

# Clone and install
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/Josh-moreton/the-alchemiser.git
cd the-alchemiser

# Install in development mode with all dependencies
make install-dev

# This installs:
# - All runtime dependencies
# - Development dependencies (pytest, black, flake8)
# - Pre-commit hooks
# - Documentation tools
```

### Development Dependencies

```bash
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Code Quality
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.5.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0

# Pre-commit hooks
pre-commit>=3.4.0
```

## Troubleshooting

### Common Installation Issues

**Python Version Error**:
```bash
# Error: Python 3.11+ required
python --version  # Check version

# Solution: Install Python 3.11+
# Use platform-specific instructions above
```

**Permission Denied**:
```bash
# Error: Permission denied during installation
# Solution: Don't use sudo with pip in virtual environment
source .venv/bin/activate
pip install -e .
```

**SSL Certificate Error**:
```bash
# Error: SSL certificate verification failed
# Solution: Update certificates
pip install --upgrade certifi
# Or use --trusted-host flags temporarily
```

**Module Not Found**:
```bash
# Error: ModuleNotFoundError after installation
# Solution: Ensure virtual environment is activated
source .venv/bin/activate
which python  # Should point to .venv/bin/python
```

### API Connection Issues

**Alpaca Authentication Failed**:
```bash
# Check API keys in .env file
cat .env | grep ALPACA

# Verify keys in Alpaca dashboard
# Ensure keys have correct permissions
```

**Network Connection Error**:
```bash
# Test basic connectivity
curl -I https://paper-api.alpaca.markets/v2/account
# Should return HTTP 200 or 401 (not connection error)

# Check firewall/proxy settings
```

### Performance Issues

**Slow Installation**:
```bash
# Use pip cache and upgrade pip
pip install --upgrade pip
pip install -e . --cache-dir ~/.pip/cache
```

**Memory Issues During Install**:
```bash
# Install dependencies individually
pip install alpaca-py
pip install typer rich
pip install -e . --no-deps
```

## Uninstallation

### Remove Virtual Environment

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment directory
rm -rf .venv

# Remove repository (if desired)
cd ..
rm -rf the-alchemiser
```

### System Cleanup

```bash
# Remove pip cache
pip cache purge

# Remove any global installations (if applicable)
pip uninstall the-alchemiser
```

## Next Steps

After successful installation:

1. **[Configuration Setup](./configuration.md)** - Configure API keys and settings
2. **[Quick Start Guide](./quickstart.md)** - Run your first trades
3. **[CLI Commands](../user-guide/cli-commands.md)** - Learn available commands

## Support

If you encounter issues:

1. Check [Troubleshooting Section](#troubleshooting) above
2. Review [GitHub Issues](https://github.com/Josh-moreton/the-alchemiser/issues)
3. Create new issue with:
   - Operating system and version
   - Python version (`python --version`)
   - Installation method used
   - Complete error message
   - Output of `alchemiser version --dependencies`
