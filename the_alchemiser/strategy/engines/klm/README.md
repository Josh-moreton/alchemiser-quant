# KLM Strategy

Ensemble strategy with multiple variants for different market conditions.

## Overview

The KLM strategy is an ensemble system that evaluates multiple strategy variants and selects the best performer based on volatility-adjusted returns. It's the most sophisticated strategy in the system.

## Strategy Architecture

1. **Ensemble Engine**: Coordinates multiple variants and selects best performer
2. **Base Variant**: Abstract base class providing common functionality
3. **Strategy Variants**: Different parameter configurations and logic patterns
4. **Performance Selection**: Chooses variant based on recent performance metrics

## Files

- `engine.py` - Ensemble orchestrator engine
- `base_variant.py` - Abstract base class for all variants
- `variants/` - Directory containing strategy variants
- `__init__.py` - Module exports

## Strategy Variants

### Current Variants (Consolidated)
- `original.py` - Baseline implementation (520/22)
- `scale_in.py` - Progressive VIX scaling (530/18)

### Legacy Variants (Being Phased Out)
- variant_410_38, variant_506_38, variant_830_21, etc.
- These will be consolidated into meaningful variants

## Common Functionality

All variants implement:
- 11-step overbought detection chain
- Single popped KMLM logic
- BSC (bond/stock/commodity) analysis  
- Combined pop bot logic
- KMLM switcher with sector comparisons
- L/S rotator for long/short positioning

## Key Symbols

### Base Requirements
- **Overbought Chain**: SPY, IOO, QQQ, VTV, XLP, XLF, RETL, TQQQ, SOXX, GLD, SLV
- **Pop Bot Logic**: TECL, SOXL, SPXL, FTEC
- **BSC Analysis**: IWM, UUP, TLT, AGG, SHY

### Variant-Specific
- **KMLM Switcher**: XLK, KMLM, SVIX (varies by variant)
- **L/S Rotator**: FTLS, SSO, UUP, SQQQ (varies by variant)

## Implementation Pattern

This strategy uses an ensemble pattern:
- Multiple variants with common interface
- Performance-based selection
- Modular variant architecture
- Complex decision trees with extensive filtering

## Consolidation Plan

The current 8 variants will be consolidated into 4 meaningful variants:
- **Original**: Baseline implementation
- **Scale-In**: Progressive VIX allocation
- **Momentum**: Momentum-focused variant  
- **Defensive**: Risk-averse variant

This will reduce code duplication while preserving strategic diversity.