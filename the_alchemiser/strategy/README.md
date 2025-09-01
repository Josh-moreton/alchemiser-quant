# Strategy Module

**Business Unit:** strategy  
**Status:** current (under construction)

## Purpose

The strategy module contains signal generation and indicator calculation for trading strategies. This module is responsible for:

- **Indicators**: Technical indicators and market signals
- **Engines**: Strategy implementations (Nuclear, TECL, etc.)  
- **Signals**: Signal processing and generation
- **Models**: ML models and data processing

## Current Status

⚠️ **No logic here yet** - This module is part of Phase 1 scaffolding for the modular architecture migration. Business logic will be moved here in Phase 2.

## Dependencies

- ✅ Allowed: `shared/` module only
- ❌ Forbidden: `portfolio/`, `execution/` modules

## Architecture Notes

This module should remain stateless where possible and communicate results via clear signal DTOs to other modules.