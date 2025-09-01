# The Alchemiser

**Advanced Multi-Strategy Quantitative Trading System**

A sophisticated algorithmic trading platform that implements multiple quantitative strategies for automated portfolio management. Built with Domain-Driven Design principles, the system provides robust execution, comprehensive error handling, and seamless integration with Alpaca Trading API.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry for dependency management
- Alpaca Trading account (paper or live)
- AWS account (for deployment)

### Installation & Setup

```bash
# Clone and enter the repository
git clone <repository-url>
cd alchemiser-quant

# Install dependencies
make dev

# Set environment variables
export PYTHONPATH="${PWD}:${PWD}/the_alchemiser:${PYTHONPATH}"

# Configure credentials (see Configuration section below)
```

### Basic Usage

```bash
# Generate trading signals (analysis mode)
make run-signals

# Execute paper trading
make run-trade

# Check account status
make status

# Execute live trading (⚠️ real money)
make run-trade-live
```

### CLI Commands

The system provides a rich command-line interface:

```bash
# Signal generation and analysis
poetry run alchemiser signal

# Multi-strategy trading execution  
poetry run alchemiser trade [--live]

# Account status and positions
poetry run alchemiser status

# DSL strategy validation
poetry run alchemiser dsl-count

# AWS Lambda deployment
poetry run alchemiser deploy

# System information
poetry run alchemiser version

# Technical indicator validation
poetry run alchemiser validate-indicators
```

## 🏗️ Current Architecture

The system follows a **Domain-Driven Design (DDD) layered architecture** with clear separation of concerns:

### Architecture Overview

```
the_alchemiser/
├── domain/              # Business logic and domain models
├── application/         # Use cases and orchestration
├── infrastructure/      # External service integrations
├── services/           # Business service implementations
├── interfaces/         # CLI and external interfaces
└── utils/              # Shared utilities
```

#### **Domain Layer** (`the_alchemiser/domain/`)
Pure business logic with no external dependencies:
- **Strategy Engines**: Nuclear, TECL, KLM trading strategies
- **Trading Entities**: Order, Position, Account models
- **Value Objects**: Symbol, Money, Percentage types
- **Domain Interfaces**: Repository contracts and protocols
- **Shared Kernel**: Common value objects and types

#### **Application Layer** (`the_alchemiser/application/`)
Orchestrates business workflows:
- **Execution**: Order placement and smart execution logic
- **Portfolio**: Portfolio rebalancing and position management
- **Mapping**: DTO/Domain object translation
- **Tracking**: Strategy performance and P&L tracking
- **Policies**: Order validation and risk management

#### **Infrastructure Layer** (`the_alchemiser/infrastructure/`)
External service integrations:
- **Alpaca Integration**: Trading API and data providers
- **AWS Services**: Lambda, S3, Secrets Manager
- **Configuration**: Environment-based settings
- **Logging**: Structured logging with context
- **Dependency Injection**: Service composition

#### **Services Layer** (`the_alchemiser/services/`)
Business service implementations:
- **Trading Services**: Order execution and position management
- **Market Data**: Real-time and historical data access
- **Error Handling**: Comprehensive error management
- **Account Services**: Portfolio and account information

#### **Interfaces Layer** (`the_alchemiser/interfaces/`)
External interfaces and user interaction:
- **CLI**: Rich command-line interface with analysis tools
- **Schemas**: Data transfer objects and API contracts

## 🧠 Trading Strategies

The system implements three sophisticated quantitative strategies:

### **Nuclear Strategy** (`StrategyType.NUCLEAR`)
- **Focus**: Energy sector and volatility hedge
- **Approach**: Nuclear energy positions with risk management
- **Allocation**: 40% default portfolio weight
- **Implementation**: `NuclearTypedEngine`

### **TECL Strategy** (`StrategyType.TECL`)
- **Focus**: Technology leverage and momentum
- **Approach**: Technology sector momentum with leveraged ETFs
- **Allocation**: 60% default portfolio weight  
- **Implementation**: `TECLStrategyEngine`

### **KLM Ensemble Strategy** (`StrategyType.KLM`)
- **Focus**: Multi-variant ensemble approach
- **Approach**: Combination of multiple strategy variants
- **Allocation**: 20% default portfolio weight
- **Implementation**: `TypedKLMStrategyEngine`

## 📊 Business Unit Classification

Every module includes a standardized docstring declaring:

```python
"""Business Unit: <unit> | Status: <status>

Module description...
"""
```

**Business Units:**
- **strategy & signal generation**: Strategy engines and signal processing
- **portfolio assessment & management**: Portfolio state and rebalancing
- **order execution/placement**: Order management and broker integration  
- **utilities**: Shared infrastructure and cross-cutting concerns

**Status Values:**
- **current**: Active, maintained code
- **legacy**: Deprecated, scheduled for removal

## ⚙️ Configuration

### Environment Variables

```bash
# Alpaca Trading API
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA__PAPER_TRADING=true  # false for live trading

# Email Notifications
EMAIL__FROM_EMAIL=your_email@domain.com
EMAIL__TO_EMAIL=recipient@domain.com

# AWS Configuration (for deployment)
AWS__REGION=eu-west-2
AWS__ACCOUNT_ID=your_account_id
SECRETS_MANAGER__SECRET_NAME=nuclear-secrets

# Strategy Configuration
STRATEGY__DEFAULT_STRATEGY_ALLOCATIONS='{"nuclear": 0.3, "tecl": 0.5, "klm": 0.2}'

# Execution Settings
EXECUTION__USE_CANONICAL_EXECUTOR=true
EXECUTION__MAX_SLIPPAGE_BPS=20.0
```

### Configuration Structure

The system uses hierarchical configuration with environment variable overrides:

```python
from the_alchemiser.infrastructure.config import load_settings

settings = load_settings()
# Access nested settings: settings.alpaca.paper_trading
```

## 🔧 Development

### Development Setup

```bash
# Install with development dependencies
make dev

# Code formatting and linting
make format
make lint

# Clean build artifacts
make clean
```

### Code Quality Standards

- **Type Safety**: 100% mypy compliance with strict settings
- **Code Formatting**: Ruff formatter with 100-character line length
- **Error Handling**: Comprehensive error categories with context
- **Documentation**: Module docstrings with business unit classification

### Development Commands

```bash
# Format code (Ruff formatter + auto-fix)
poetry run ruff format the_alchemiser/
poetry run ruff check --fix the_alchemiser/

# Type checking
poetry run mypy the_alchemiser/

# Linting
poetry run ruff check the_alchemiser/
```

## 🚀 Deployment

### AWS Lambda Deployment

The system is designed for serverless deployment on AWS Lambda:

```bash
# Deploy to AWS Lambda
make deploy
# or
poetry run alchemiser deploy
```

### Infrastructure Components

- **AWS Lambda**: Main execution environment
- **EventBridge Scheduler**: Automated trading triggers
- **S3**: Configuration and data storage
- **Secrets Manager**: Secure credential storage
- **CloudWatch**: Logging and monitoring

### Configuration Files

- `template.yaml`: AWS SAM infrastructure definition
- `samconfig.toml`: Deployment configuration
- `pyproject.toml`: Python dependencies and tool configuration

## 🔍 Error Handling & Monitoring

### Error Categories

The system categorizes errors for appropriate handling:

- **CRITICAL**: System-level failures that stop all operations
- **TRADING**: Order execution, position validation issues
- **DATA**: Market data, API connectivity issues
- **STRATEGY**: Strategy calculation, signal generation issues
- **CONFIGURATION**: Config, authentication, setup issues
- **NOTIFICATION**: Email, alert delivery issues
- **WARNING**: Non-critical issues that don't stop execution

### Error Handling Usage

```python
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler

error_handler = TradingSystemErrorHandler()
error_details = error_handler.handle_error(
    error=exception,
    component="ComponentName.method_name", 
    context="operation_description",
    additional_data={"symbol": "AAPL", "qty": 100}
)
```

### Monitoring & Alerts

- **Email Notifications**: Automatic alerts with categorization and remediation steps
- **Structured Logging**: Context-aware logging with request IDs
- **Circuit Breakers**: Automatic failure handling and recovery

## 🔄 Future Architecture (Target State)

> **Migration Planned**: The system is planned to migrate to a **four-module architecture** as defined in `.github/copilot-instructions.md`:

```
strategy/     # Signal generation and indicators  
portfolio/    # Portfolio state and rebalancing
execution/    # Broker integrations and order placement
shared/       # DTOs, utilities, cross-cutting concerns
```

### Target Module Structure

```
strategy/
├── indicators/              # Technical indicators, market signals
├── engines/                 # Strategy implementations
├── signals/                 # Signal processing and generation
└── models/                  # ML models and data processing

portfolio/  
├── positions/               # Position tracking and management
├── rebalancing/             # Rebalancing algorithms and logic
├── valuation/               # Portfolio valuation and metrics
└── risk/                    # Risk management and constraints

execution/
├── brokers/                 # Broker API integrations
├── orders/                  # Order management and lifecycle
├── strategies/              # Smart execution strategies  
└── routing/                 # Order routing and placement

shared/
├── dtos/                    # Data transfer objects
├── types/                   # Common value objects
├── utils/                   # Utility functions and helpers
├── config/                  # Configuration management
└── logging/                 # Logging setup and utilities
```

This migration will provide:
- **Cleaner Module Boundaries**: Strict dependency rules
- **Improved Maintainability**: Clear separation of concerns
- **Enhanced Testability**: Better isolation for unit testing
- **Consistent API Design**: Standardized interfaces across modules

## 📚 Key Files Reference

### Entry Points
- `main.py`: Local execution entry point
- `lambda_handler.py`: AWS Lambda entry point
- `interfaces/cli/cli.py`: Command-line interface

### Core Configuration
- `infrastructure/config/config.py`: Application settings
- `template.yaml`: AWS infrastructure definition
- `pyproject.toml`: Dependencies and tool configuration

### Strategy Implementation
- `domain/registry/strategy_registry.py`: Strategy configuration
- `domain/strategies/`: Strategy engine implementations
- `application/execution/`: Order execution logic

### Error Handling
- `services/errors/handler.py`: Central error handling
- `services/errors/exceptions.py`: Custom exception definitions

## 🤖 AI Agent Guidelines

This repository is optimized for AI-driven development:

### Code Generation Standards
- Follow business unit docstring requirements
- Use explicit typing for all functions
- Implement comprehensive error handling
- Maintain DDD architectural boundaries

### Import Guidelines
- Use public module APIs, not deep imports
- Import from layer interfaces, not implementations
- Follow dependency direction: domain ← application ← infrastructure

### Error Handling Patterns
```python
# Critical errors should bubble up
try:
    result = strategy.calculate()
except StrategyError as e:
    if e.severity == ErrorSeverity.CRITICAL:
        raise
    else:
        logger.warning(f"Non-critical error: {e}")
        return safe_fallback_value
```

For AI agents working on this codebase, refer to `.github/copilot-instructions.md` for detailed architectural guidance and coding standards.

---

**Version**: 2.0.0  
**License**: MIT  
**Author**: Josh Moreton