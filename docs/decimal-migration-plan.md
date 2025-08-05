# Decimal Migration Plan for Financial Precision

## Overview

This document outlines a comprehensive plan to migrate The Alchemiser quantitative trading system from `float` and `str | float` types to Python's `Decimal` type for precise financial calculations. This migration addresses floating-point precision issues that can accumulate in trading operations and aligns with financial industry best practices.

## Why Decimal?

### Current Issues with Float

- **Precision Loss**: `0.1 + 0.2 != 0.3` in floating-point arithmetic
- **Rounding Errors**: Accumulate over multiple calculations
- **Regulatory Compliance**: Financial systems require exact decimal representation
- **Money Calculations**: Trading systems need precise penny calculations

### Benefits of Decimal

- **Exact Precision**: No floating-point representation errors
- **Configurable Precision**: Set decimal places as needed (typically 2-8 for finance)
- **Industry Standard**: Used by all major financial systems
- **Regulatory Compliance**: Meets financial regulatory requirements

## Migration Scope Assessment

### High Priority Files (Core Financial Logic)

1. **`the_alchemiser/core/types.py`** - Core type definitions
2. **`the_alchemiser/utils/trading_math.py`** - Mathematical calculations
3. **`the_alchemiser/execution/portfolio_rebalancer.py`** - Portfolio calculations
4. **`the_alchemiser/execution/trading_engine.py`** - Order value calculations
5. **`the_alchemiser/execution/alpaca_client.py`** - API integration layer

### Medium Priority Files (Display & Reporting)

6. **`the_alchemiser/core/ui/cli_formatter.py`** - Console output formatting
7. **`the_alchemiser/execution/reporting.py`** - Trade summaries
8. **`the_alchemiser/utils/dashboard_utils.py`** - Dashboard data
9. **`the_alchemiser/utils/portfolio_pnl_utils.py`** - P&L calculations

### Low Priority Files (Utilities & Extensions)

10. **Email templates** - Formatting for email reports
11. **Dashboard components** - Frontend display helpers
12. **Logging utilities** - Debug output formatting

## Phase-by-Phase Implementation Plan

### Phase 1: Foundation Setup (Week 1)

#### 1.1 Create Decimal Configuration Module

```python
# the_alchemiser/core/decimal_config.py
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Configure global decimal context
getcontext().prec = 28  # High precision for intermediate calculations
getcontext().rounding = ROUND_HALF_UP

# Standard precisions for different use cases
CURRENCY_PRECISION = Decimal('0.01')       # $0.01 - standard currency
SHARE_PRECISION = Decimal('0.000001')     # 6 decimal places for shares
PERCENTAGE_PRECISION = Decimal('0.0001')   # 0.01% - 4 decimal places
PRICE_PRECISION = Decimal('0.0001')       # $0.0001 - 4 decimal places

def currency_decimal(value: str | float | int) -> Decimal:
    """Convert to currency Decimal with 2 decimal places."""
    return Decimal(str(value)).quantize(CURRENCY_PRECISION)

def share_decimal(value: str | float | int) -> Decimal:
    """Convert to share quantity Decimal with 6 decimal places."""
    return Decimal(str(value)).quantize(SHARE_PRECISION)

def percentage_decimal(value: str | float | int) -> Decimal:
    """Convert to percentage Decimal with 4 decimal places."""
    return Decimal(str(value)).quantize(PERCENTAGE_PRECISION)

def price_decimal(value: str | float | int) -> Decimal:
    """Convert to price Decimal with 4 decimal places."""
    return Decimal(str(value)).quantize(PRICE_PRECISION)
```

#### 1.2 Update Core Types

```python
# the_alchemiser/core/types.py
from decimal import Decimal

class AccountInfo(TypedDict):
    account_id: str
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    day_trades_remaining: int
    portfolio_value: Decimal
    last_equity: Decimal
    daytrading_buying_power: Decimal
    regt_buying_power: Decimal
    status: Literal["ACTIVE", "INACTIVE"]

class PositionInfo(TypedDict):
    symbol: str
    qty: Decimal  # Share quantities
    side: Literal["long", "short"]
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pl: Decimal
    unrealized_plpc: Decimal  # Percentage as decimal (0.05 = 5%)
    current_price: Decimal

class OrderDetails(TypedDict):
    id: str
    symbol: str
    qty: Decimal
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: Literal["new", "partially_filled", "filled", "canceled", "expired", "rejected"]
    filled_qty: Decimal
    filled_avg_price: Decimal | None
    created_at: str
    updated_at: str
```

#### 1.3 Create Conversion Utilities

```python
# the_alchemiser/utils/decimal_converters.py
from decimal import Decimal
from typing import Any
from ..core.decimal_config import currency_decimal, share_decimal, price_decimal

def convert_alpaca_account(raw_account: dict[str, Any]) -> dict[str, Any]:
    """Convert Alpaca account data to Decimal format."""
    return {
        'account_id': raw_account.get('id', ''),
        'equity': currency_decimal(raw_account.get('equity', 0)),
        'cash': currency_decimal(raw_account.get('cash', 0)),
        'buying_power': currency_decimal(raw_account.get('buying_power', 0)),
        'portfolio_value': currency_decimal(raw_account.get('portfolio_value', 0)),
        # ... other fields
    }

def convert_alpaca_position(raw_position: dict[str, Any]) -> dict[str, Any]:
    """Convert Alpaca position data to Decimal format."""
    return {
        'symbol': raw_position.get('symbol', ''),
        'qty': share_decimal(raw_position.get('qty', 0)),
        'market_value': currency_decimal(raw_position.get('market_value', 0)),
        'cost_basis': currency_decimal(raw_position.get('cost_basis', 0)),
        'current_price': price_decimal(raw_position.get('current_price', 0)),
        # ... other fields
    }
```

### Phase 2: Core Financial Logic (Week 2)

#### 2.1 Update Trading Math

```python
# the_alchemiser/utils/trading_math.py
from decimal import Decimal
from ..core.decimal_config import currency_decimal, percentage_decimal

def calculate_rebalance_amounts(
    target_portfolio: dict[str, Decimal],  # Target percentages as decimals
    current_values: dict[str, Decimal],    # Current dollar values
    total_portfolio_value: Decimal
) -> dict[str, dict[str, Any]]:
    """Calculate rebalancing trades with Decimal precision."""
    
    rebalance_plan = {}
    
    for symbol, target_percentage in target_portfolio.items():
        current_value = current_values.get(symbol, Decimal('0'))
        target_value = total_portfolio_value * target_percentage
        trade_amount = target_value - current_value
        
        # Use percentage threshold for rebalancing decision
        threshold = total_portfolio_value * Decimal('0.01')  # 1% threshold
        needs_rebalance = abs(trade_amount) > threshold
        
        rebalance_plan[symbol] = {
            'current_value': current_value,
            'target_value': target_value,
            'trade_amount': trade_amount,
            'current_weight': current_value / total_portfolio_value if total_portfolio_value > 0 else Decimal('0'),
            'target_weight': target_percentage,
            'needs_rebalance': needs_rebalance
        }
    
    return rebalance_plan
```

#### 2.2 Update Portfolio Rebalancer

Key changes needed:

- Convert all float calculations to Decimal
- Update quantity calculations for precise share amounts
- Ensure proper rounding for order sizes

#### 2.3 Update Order Value Calculations

- Notional order amounts
- Commission calculations
- Buying power validations

### Phase 3: API Integration Layer (Week 3)

#### 3.1 Alpaca Client Conversion Layer

```python
# the_alchemiser/execution/alpaca_client.py
from decimal import Decimal
from ..utils.decimal_converters import convert_alpaca_account, convert_alpaca_position

class AlpacaClient:
    def get_account_info(self) -> AccountInfo:
        """Get account info with Decimal conversion."""
        raw_account = self.trading_client.get_account()
        return convert_alpaca_account(raw_account)
    
    def get_positions_dict(self) -> dict[str, PositionInfo]:
        """Get positions with Decimal conversion."""
        raw_positions = self.trading_client.get_all_positions()
        converted_positions = {}
        
        for pos in raw_positions:
            converted_pos = convert_alpaca_position(pos)
            converted_positions[converted_pos['symbol']] = converted_pos
            
        return converted_positions
    
    def place_order_decimal(
        self, 
        symbol: str, 
        notional: Decimal,  # Use Decimal for notional amounts
        side: OrderSide
    ) -> str | None:
        """Place order with Decimal precision."""
        # Convert Decimal to string for API call
        notional_str = str(notional.quantize(currency_decimal('0.01')))
        return self._place_order_internal(symbol, notional_str, side)
```

#### 3.2 Error Handling for Conversion

- Handle conversion errors gracefully
- Provide fallback mechanisms
- Log conversion issues for debugging

### Phase 4: Display and Formatting (Week 4)

#### 4.1 Update CLI Formatter

```python
# the_alchemiser/core/ui/cli_formatter.py
from decimal import Decimal

def format_currency(value: Decimal) -> str:
    """Format Decimal currency for display."""
    return f"${value:,.2f}"

def format_percentage(value: Decimal) -> str:
    """Format Decimal percentage for display."""
    return f"{(value * 100):,.2f}%"

def format_shares(value: Decimal) -> str:
    """Format Decimal share quantity for display."""
    if value % 1 == 0:
        return f"{value:,.0f}"  # Whole shares
    else:
        return f"{value:,.6f}".rstrip('0').rstrip('.')  # Fractional shares
```

#### 4.2 Update Dashboard Utils

- Convert display calculations to use Decimal
- Ensure proper formatting for web display
- Update chart data preparation

### Phase 5: Testing and Validation (Week 5)

#### 5.1 Unit Tests for Decimal Operations

```python
# tests/test_decimal_precision.py
import pytest
from decimal import Decimal
from the_alchemiser.utils.trading_math import calculate_rebalance_amounts

def test_precise_rebalancing_calculation():
    """Test that rebalancing calculations are precise."""
    target_portfolio = {
        'AAPL': Decimal('0.333333'),  # 33.3333%
        'GOOGL': Decimal('0.333333'),
        'MSFT': Decimal('0.333334')   # 33.3334% (totals 100%)
    }
    
    total_value = Decimal('10000.00')
    current_values = {
        'AAPL': Decimal('3500.00'),
        'GOOGL': Decimal('3200.00'),
        'MSFT': Decimal('3300.00')
    }
    
    result = calculate_rebalance_amounts(target_portfolio, current_values, total_value)
    
    # Verify precise calculations
    assert result['AAPL']['target_value'] == Decimal('3333.33')
    assert result['GOOGL']['target_value'] == Decimal('3333.33')
    assert result['MSFT']['target_value'] == Decimal('3333.34')
    
    # Verify total adds up exactly
    total_target = sum(item['target_value'] for item in result.values())
    assert total_target == total_value
```

#### 5.2 Integration Tests

- Test full trading workflow with Decimal precision
- Verify API integration works correctly
- Test edge cases and error handling

#### 5.3 Performance Testing

- Benchmark Decimal vs float performance
- Ensure acceptable performance impact
- Optimize critical calculation paths

### Phase 6: Documentation and Deployment (Week 6)

#### 6.1 Update Documentation

- Document new Decimal configuration
- Update API documentation
- Create migration guide for developers

#### 6.2 Backward Compatibility

- Provide migration utilities for existing data
- Support gradual rollout if needed
- Create rollback procedures

## Implementation Challenges and Solutions

### Challenge 1: API Integration

**Problem**: Alpaca API returns float values
**Solution**: Create conversion layer that immediately converts API responses to Decimal

### Challenge 2: Performance Impact

**Problem**: Decimal operations are slower than float
**Solution**:

- Use Decimal only for financial calculations
- Keep float for non-financial operations (timestamps, counters)
- Optimize critical calculation paths

### Challenge 3: Serialization

**Problem**: JSON doesn't natively support Decimal
**Solution**:

- Convert to string for JSON serialization
- Use custom JSON encoders/decoders
- Document serialization format

### Challenge 4: Database Storage

**Problem**: Existing data may be in float format
**Solution**:

- Create migration scripts for existing data
- Use DECIMAL/NUMERIC database types for new data
- Maintain backward compatibility during transition

## Risk Mitigation

### Low Risk Mitigations

1. **Extensive Testing**: Comprehensive unit and integration tests
2. **Gradual Rollout**: Implement phase by phase
3. **Monitoring**: Add logging for conversion operations
4. **Rollback Plan**: Keep ability to revert to float types

### Medium Risk Mitigations

1. **Performance Monitoring**: Track calculation performance
2. **Data Validation**: Verify calculations match expected results
3. **Error Handling**: Graceful handling of conversion errors

### High Risk Mitigations

1. **Backup Strategy**: Full backup before migration
2. **Testing Environment**: Complete testing in paper trading
3. **Phased Deployment**: Deploy to paper trading first, then live

## Success Criteria

### Phase Completion Criteria

- [ ] All financial calculations use Decimal types
- [ ] API integration layer converts all financial data
- [ ] Display formatting works correctly with Decimal
- [ ] All tests pass with new types
- [ ] Performance impact is acceptable (<10% slowdown)
- [ ] Documentation is updated

### Quality Assurance

- [ ] No precision loss in financial calculations
- [ ] All monetary values display correctly
- [ ] Trading operations produce exact results
- [ ] P&L calculations are precise to the penny

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1 | Week 1 | Foundation setup, core types updated |
| 2 | Week 2 | Trading math and rebalancing logic |
| 3 | Week 3 | API integration layer complete |
| 4 | Week 4 | Display and formatting updated |
| 5 | Week 5 | Testing and validation complete |
| 6 | Week 6 | Documentation and deployment ready |

**Total Estimated Time**: 6 weeks with 1 developer working part-time (2-3 hours/day)

## Post-Migration Benefits

1. **Regulatory Compliance**: Meet financial industry standards
2. **Precision Trading**: Eliminate floating-point errors
3. **Professional Grade**: Industry-standard financial calculations
4. **Audit Trail**: Exact financial records for compliance
5. **Scalability**: Robust foundation for larger trading operations

## Conclusion

This migration represents a significant improvement in the financial accuracy and professional standards of The Alchemiser trading system. While requiring substantial effort, the benefits of precise financial calculations justify the investment, particularly for a system handling real money in trading operations.

The phased approach minimizes risk while ensuring thorough testing and validation at each stage. Upon completion, the system will meet professional financial software standards and eliminate the potential for precision-related trading errors.
