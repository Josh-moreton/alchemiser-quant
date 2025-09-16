# Typing Guidelines for Alchemiser Quant

## Overview

This guide provides developers with practical guidelines for maintaining type safety and following the typing architecture defined in [TYPING_ARCHITECTURE_RULES.md](../TYPING_ARCHITECTURE_RULES.md).

## Layer Ownership Table

| Layer | Type Used | Purpose | Examples |
|-------|-----------|---------|----------|
| External SDK | `TradeAccount`, `Order`, `Position` | Rich API objects | Alpaca SDK objects |
| Execution Layer | `AccountInfoDTO`, `PriceCalculationResultDTO` | Domain representation | Order execution, price calculation |
| Strategy Layer | `StrategySignalDTO`, `TechnicalIndicatorsDTO` | Strategy outputs | Signal generation, indicators |
| Portfolio Layer | `PortfolioStateDTO`, `PositionDTO` | Portfolio state | State tracking, rebalancing |
| Shared/Protocol | Domain DTOs | Cross-module interface | Communication contracts |
| Orchestration | Domain DTOs | Business logic | Workflow coordination |
| Serialization | `dict[str, str\|int\|bool]` | JSON/transport only | API responses, persistence |

## Allowed `Any` Contexts

### ✅ Acceptable Uses (with `# noqa: ANN401`)

1. **External SDK Integration**
```python
def trading_client(self) -> Any:  # noqa: ANN401  # External broker SDK object
    """Access to underlying trading client for backward compatibility."""
```

2. **Serialization Metadata**
```python
class MyDTO(BaseModel):
    metadata: dict[str, Any] | None = None  # noqa: ANN401  # Flexible metadata
```

3. **AWS Lambda Context**
```python
def lambda_handler(event: LambdaEventDTO, context: Any = None) -> dict[str, Any]:  # noqa: ANN401
    """AWS Lambda context is external object."""
```

4. **Protocol Structural Typing**
```python
class _ModelDumpProtocol(Protocol):
    def model_dump(self) -> dict[str, Any]: ...  # noqa: ANN401  # Structural typing
```

### ❌ Prohibited Uses

1. **Business Logic Parameters**
```python
# ❌ NEVER
def process_signals(signals: Any) -> dict[str, float]:

# ✅ DO THIS
def process_signals(signals: list[StrategySignalDTO]) -> dict[str, float]:
```

2. **Return Types in Domain Methods**
```python
# ❌ NEVER
def get_account(self) -> Any:

# ✅ DO THIS
def get_account(self) -> AccountInfoDTO | None:
```

3. **DTO Fields Without Constraints**
```python
# ❌ NEVER
class MyDTO(BaseModel):
    data: Any

# ✅ DO THIS
class MyDTO(BaseModel):
    data: str | int | float | None
```

## DTO Conversion Examples

### Example 1: Strategy Signal Conversion

```python
# ❌ Old way (dict-based)
def generate_signals(self) -> dict[str, Any]:
    return {
        "strategy_name": "nuclear",
        "symbol": "TQQQ",
        "action": "BUY",
        "confidence": 0.8
    }

# ✅ New way (DTO-based)
def generate_signals(self) -> StrategySignalDTO:
    return StrategySignalDTO(
        correlation_id="signal_123",
        causation_id="trigger_456",
        timestamp=datetime.now(UTC),
        symbol="TQQQ",
        action="BUY",
        confidence=Decimal("0.8"),
        reasoning="Nuclear strategy signal",
        strategy_name="nuclear"
    )
```

### Example 2: Price Calculation Conversion

```python
# ❌ Old way (tuple + dict)
def calculate_price(quote: Quote, side: str) -> tuple[Decimal, dict[str, Any]]:
    price = calculate_optimal_price(quote, side)
    metadata = {
        "spread_pct": 0.1,
        "confidence": 0.8,
        "method": "liquidity_aware"
    }
    return price, metadata

# ✅ New way (DTO-based)
def calculate_price(quote: Quote, side: str) -> PriceCalculationResultDTO:
    price = calculate_optimal_price(quote, side)
    metadata = PriceCalculationMetadataDTO(
        spread_pct=0.1,
        bid_ask_ratio=0.95,
        volume_ratio=0.5,
        bid_volume=1000.0,
        ask_volume=1200.0,
        calculation_method="liquidity_aware"
    )
    return PriceCalculationResultDTO(
        anchor_price=price,
        metadata=metadata
    )
```

### Example 3: Technical Indicators Conversion

```python
# ❌ Old way (dict[str, Any])
def calculate_indicators(self, market_data: dict[str, Any]) -> dict[str, Any]:
    indicators = {}
    for symbol, df in market_data.items():
        indicators[symbol] = {
            "rsi_10": calculate_rsi(df, 10),
            "ma_200": calculate_ma(df, 200),
            "current_price": df["Close"].iloc[-1]
        }
    return indicators

# ✅ New way (specific types)
def calculate_indicators(self, market_data: dict[str, pd.DataFrame]) -> dict[str, dict[str, float | None]]:
    indicators = {}
    for symbol, df in market_data.items():
        indicators[symbol] = {
            "rsi_10": calculate_rsi(df, 10),
            "ma_200": calculate_ma(df, 200),  
            "current_price": float(df["Close"].iloc[-1])
        }
    return indicators
```

## Migration Patterns

### Pattern 1: Replace `Any` with Union Types

```python
# ❌ Before
def convert_value(value: Any) -> Decimal:
    return Decimal(str(value))

# ✅ After  
def convert_value(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value))
```

### Pattern 2: Replace `dict[str, Any]` with Specific Types

```python
# ❌ Before
def process_config(config: dict[str, Any]) -> bool:
    return config.get("enabled", False)

# ✅ After
def process_config(config: dict[str, str | int | bool]) -> bool:
    return bool(config.get("enabled", False))
```

### Pattern 3: Create DTOs for Complex Data

```python
# ❌ Before
def get_execution_summary(self) -> dict[str, Any]:
    return {
        "total_orders": 5,
        "success_rate": 0.8,
        "metadata": {"strategy": "nuclear"}
    }

# ✅ After
def get_execution_summary(self) -> ExecutionSummaryDTO:
    return ExecutionSummaryDTO(
        total_orders=5,
        success_rate=Decimal("0.8"),
        correlation_id="exec_123",
        timestamp=datetime.now(UTC),
        strategy_name="nuclear"
    )
```

## Common Gotchas

### 1. Pydantic Field Annotations
```python
# ❌ Wrong
class MyDTO(BaseModel):
    data: Any = Field(...)

# ✅ Correct
class MyDTO(BaseModel):
    data: dict[str, str | int] = Field(...)
```

### 2. Optional vs Required Fields
```python
# ❌ Wrong
class MyDTO(BaseModel):
    optional_field: Any | None = None

# ✅ Correct  
class MyDTO(BaseModel):
    optional_field: str | int | None = None
```

### 3. Serialization Helpers
```python
# ✅ Acceptable for transport layer
def to_dict(self) -> dict[str, Any]:  # noqa: ANN401  # Serialization only
    return self.model_dump()

# ✅ Better - be more specific when possible
def to_api_response(self) -> dict[str, str | int | float]:
    return {
        "symbol": self.symbol,
        "price": float(self.price),
        "quantity": self.quantity
    }
```

## Tools and Validation

### Run Typing Audit
```bash
# Check all violations
python tools/typing_audit.py the_alchemiser/

# Check if CI would pass
python tools/check_fail_on_severity.py report/typing_violations.json
```

### Run MyPy
```bash
mypy the_alchemiser/ --config-file=pyproject.toml
```

### Run Ruff Type Checks  
```bash
ruff check the_alchemiser/ --select=ANN
```

## Integration with CI/CD

The typing audit is integrated into GitHub Actions and will fail the build if:

- **CRITICAL violations > 0**: Protocol methods returning `Any` without proper documentation
- **HIGH violations > 10**: Business logic using `Any` or `dict[str, Any]`

Current thresholds can be adjusted in `tools/check_fail_on_severity.py` as violations are fixed.

## Best Practices

1. **Start with DTOs**: When adding new features, define DTOs first
2. **Use specific dict types**: Replace `dict[str, Any]` with `dict[str, str | int | bool]`
3. **Document `Any` usage**: Always include `# noqa: ANN401` with justification
4. **Leverage Union types**: Use `str | int | float` instead of `Any` for flexible inputs
5. **Protocol boundaries**: Use DTOs at module boundaries, specific types internally
6. **Gradual migration**: Update return types first, then parameters, then callers

## Getting Help

- Review [TYPING_ARCHITECTURE_RULES.md](../TYPING_ARCHITECTURE_RULES.md) for detailed rules
- Check existing DTOs in `the_alchemiser/shared/dto/` for patterns
- Run the typing audit tool for specific violation suggestions
- Ask in code reviews for guidance on complex typing scenarios