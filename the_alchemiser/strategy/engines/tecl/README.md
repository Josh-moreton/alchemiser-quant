# TECL Strategy

Technology leverage and momentum strategy implementation.

## Overview

The TECL strategy ("TECL For The Long Term v7") is designed for long-term technology leverage with volatility protection and market regime detection.

## Strategy Logic

1. **Market Regime Detection**: SPY vs 200-day MA (bull vs bear market)
2. **Volatility Protection**: Multiple RSI-based triggers for defensive positions
3. **Technology Focus**: TECL as primary growth vehicle in appropriate conditions
4. **Bond Hedge**: BIL as defensive cash equivalent
5. **Sector Rotation**: XLK vs KMLM comparison for technology timing

## Files

- `engine.py` - Main strategy engine (self-contained)
- `__init__.py` - Module exports

## Key Symbols

- **TECL**: 3x leveraged technology ETF (primary growth vehicle)
- **BIL**: Short-term treasury bills (defensive cash equivalent)  
- **UVXY**: Volatility hedge for extreme overbought conditions
- **XLK**: Technology sector ETF (timing signal)
- **KMLM**: Materials sector ETF (comparative signal)
- **Market Indicators**: TQQQ, SPXL, SPY, SQQQ, BSV

## Strategy Summary

### Bull Market (SPY > 200 MA)
1. If TQQQ RSI > 79 → 25% UVXY + 75% BIL (volatility hedge)
2. If SPY RSI > 80 → 25% UVXY + 75% BIL (volatility hedge)
3. KMLM Switcher logic for technology timing

### Bear Market (SPY < 200 MA)
1. If TQQQ RSI < 31 → TECL (buy tech dip)
2. If SPXL RSI < 29 → SPXL (buy S&P dip)
3. If UVXY conditions met → volatility plays
4. KMLM Switcher for defensive positioning

## Implementation Pattern

This strategy uses a monolithic design with all logic contained in the engine file. Future refactoring may extract pure logic to separate file following Nuclear pattern.