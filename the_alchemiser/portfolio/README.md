# Portfolio Module

**Business Unit:** portfolio  
**Status:** current (under construction)

## Purpose

The portfolio module handles portfolio state management and rebalancing logic. This module is responsible for:

- **Positions**: Position tracking and management
- **Rebalancing**: Rebalancing algorithms and logic
- **Valuation**: Portfolio valuation and metrics  
- **Risk**: Risk management and constraints

## Current Status

⚠️ **No logic here yet** - This module is part of Phase 1 scaffolding for the modular architecture migration. Business logic will be moved here in Phase 2.

## Dependencies

- ✅ Allowed: `shared/` module only
- ❌ Forbidden: `strategy/`, `execution/` modules

## Architecture Notes

This module manages all portfolio state and positions, handles rebalancing calculations and constraints, and provides portfolio analytics. It should never directly place orders (delegates to execution module).