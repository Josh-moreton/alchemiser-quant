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

## 🏗️ Architecture

The system follows a **modular architecture** with four top-level modules and strict dependency rules:

### Architecture Overview

```
strategy/                # Signal generation and indicators
portfolio/               # Portfolio state and rebalancing
execution/              # Broker integrations and order placement
shared/                 # DTOs, utilities, cross-cutting concerns
```

#### **Strategy Module** (`strategy/`)
Signal generation, indicator calculation, ML models, regime detection:
- **Indicators**: Technical indicators, market signals (`strategy/indicators/`)
- **Engines**: Strategy implementations - Nuclear, TECL, KLM (`strategy/engines/`)
- **Signals**: Signal processing and generation (`strategy/signals/`)
- **Models**: ML models and data processing (`strategy/models/`)

#### **Portfolio Module** (`portfolio/`)
Portfolio state management, sizing, rebalancing logic, risk management:
- **Positions**: Position tracking and management (`portfolio/positions/`)
- **Rebalancing**: Rebalancing algorithms and logic (`portfolio/rebalancing/`)
- **Valuation**: Portfolio valuation and metrics (`portfolio/valuation/`)
- **Risk**: Risk management and constraints (`portfolio/risk/`)

#### **Execution Module** (`execution/`)
Broker API integrations, order placement, smart execution, error handling:
- **Brokers**: Broker API integrations - Alpaca integration (`execution/brokers/`)
- **Orders**: Order management and lifecycle (`execution/orders/`)
- **Strategies**: Smart execution strategies (`execution/strategies/`)
- **Routing**: Order routing and placement (`execution/routing/`)

#### **Shared Module** (`shared/`)
DTOs, utilities, logging, cross-cutting concerns, common value objects:
- **DTOs**: Data transfer objects (`shared/dtos/`)
- **Types**: Common value objects - Money, Symbol classes (`shared/types/`)
- **Utils**: Utility functions and helpers (`shared/utils/`)
- **Config**: Configuration management (`shared/config/`)
- **Logging**: Logging setup and utilities (`shared/logging/`)

### Module Dependency Rules

```
✅ Allowed Dependencies:
- strategy/ → shared/
- portfolio/ → shared/  
- execution/ → shared/

❌ Forbidden Dependencies:
- strategy/ → portfolio/
- strategy/ → execution/
- portfolio/ → execution/
- shared/ → any other module
```

### Inter-Module Communication

Modules communicate via well-defined DTOs and interfaces:
- **Strategy** generates signals consumed by **Portfolio**
- **Portfolio** creates execution plans consumed by **Execution**
- All communication through explicit contracts, not shared state
- Use correlation IDs for traceability across module boundaries

### Current Implementation Status

> **Note**: The codebase is currently migrating to this four-module architecture. New development should follow the modular structure above. The current implementation uses a DDD layered architecture that is being refactored into these modules.

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

**Business Units (aligned with modules):**
- **strategy**: Signal generation, indicators, ML models
- **portfolio**: Portfolio state, sizing, rebalancing logic
- **execution**: Broker API integrations, order placement, error handling
- **shared**: DTOs, utilities, logging, cross-cutting concerns

**Status Values:**
- **current**: Active, maintained code
- **legacy**: Deprecated, scheduled for removal

**Example Module Docstrings:**

```python
# strategy module
"""Business Unit: strategy | Status: current

Signal generation and indicator calculation for trading strategies.
"""

# portfolio module  
"""Business Unit: portfolio | Status: current

Portfolio state management and rebalancing logic.
"""

# execution module
"""Business Unit: execution | Status: current

Broker API integrations and order placement.
"""

# shared module
"""Business Unit: shared | Status: current

DTOs, utilities, and cross-cutting concerns.
"""
```

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

## 📚 Key Files Reference

### Entry Points
- `main.py`: Local execution entry point
- `lambda_handler.py`: AWS Lambda entry point
- `interfaces/cli/cli.py`: Command-line interface

### Core Configuration
- `shared/config/`: Application settings and configuration management
- `template.yaml`: AWS infrastructure definition
- `pyproject.toml`: Dependencies and tool configuration

### Strategy Implementation
- `strategy/engines/`: Strategy engine implementations (Nuclear, TECL, KLM)
- `strategy/indicators/`: Technical indicators and signal processing
- `portfolio/rebalancing/`: Portfolio rebalancing and allocation logic

### Error Handling
- `shared/utils/`: Error handling utilities and patterns
- Module-specific error types with context

## 🤖 AI Agent Guidelines

This repository is optimized for AI-driven development:

### Code Generation Standards
- Follow business unit docstring requirements (strategy|portfolio|execution|shared)
- Use explicit typing for all functions (100% mypy compliance)
- Implement comprehensive error handling with module context
- Maintain modular architectural boundaries

### Import Guidelines & Module Isolation
```python
# ✅ Allowed imports
from shared.types import Money, Symbol
from strategy.indicators import MovingAverage
from portfolio.positions import PositionTracker
from execution.brokers import AlpacaConnector

# ❌ Forbidden imports
from strategy.internal.calculations import sma  # Deep import
from portfolio import rebalance_portfolio  # Cross-module import
```

### Module Placement Guidelines
- **New indicator (SMA, RSI, etc.)** → `strategy/indicators/`
- **New strategy engine** → `strategy/engines/`
- **New broker connector** → `execution/brokers/`
- **Portfolio rebalancing logic** → `portfolio/rebalancing/`
- **New position tracker** → `portfolio/positions/`
- **Order execution strategy** → `execution/strategies/`
- **Common DTO classes** → `shared/dtos/`
- **Utility functions** → `shared/utils/`
- **Configuration types** → `shared/config/`

### Error Handling Patterns
```python
# Module-specific error types with context
from shared.errors import StrategyError, PortfolioError, ExecutionError

try:
    result = strategy.calculate()
except StrategyError as e:
    logger.error(f"Strategy error", extra={"module": "strategy.indicators.sma"})
    if e.severity == ErrorSeverity.CRITICAL:
        raise
    return safe_fallback_value
```

### Dependency Rules
- **strategy/** may only import from **shared/**
- **portfolio/** may only import from **shared/**
- **execution/** may only import from **shared/**
- **shared/** must not import from any other module
- Cross-module communication via DTOs and interfaces only

For complete architectural guidance and coding standards, refer to `.github/copilot-instructions.md`.

---

**Version**: 2.0.0  
**License**: MIT  
**Author**: Josh Moreton