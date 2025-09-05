# Nuclear Strategy

Nuclear energy and volatility hedge strategy implementation.

## Overview

The Nuclear strategy focuses on nuclear energy stocks with volatility protection through SPY RSI monitoring and defensive positioning during extreme market conditions.

## Strategy Logic

1. **Market Regime Detection**: SPY RSI monitoring for overbought/oversold conditions
2. **Volatility Protection**: UVXY/BTAL portfolio for extreme overbought conditions
3. **Nuclear Focus**: Nuclear energy stocks as primary growth vehicle in bull markets
4. **Tech Hedge**: TQQQ for oversold bounce opportunities

## Files

- `engine.py` - Main strategy engine inheriting from StrategyEngine
- `logic.py` - Pure evaluation logic (side-effect free)
- `__init__.py` - Module exports

## Key Symbols

- **Nuclear Stocks**: SMR, BWXT, LEU, EXC, NLR, OKLO
- **Market Indicators**: SPY, IOO, TQQQ, VTV, XLF, VOX
- **Volatility Hedge**: UVXY, BTAL
- **Tech Stocks**: QQQ, SQQQ, PSQ, UPRO
- **Bonds**: TLT, IEF

## Implementation Pattern

This strategy follows the standardized pattern:
- Pure logic in `logic.py` for easy testing
- Infrastructure handling in `engine.py`
- Clean separation of concerns
- Type-safe interfaces