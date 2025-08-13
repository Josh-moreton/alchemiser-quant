# Portfolio Rebalancer Modernization Plan

## 🎯 Current Problems

### Architectural Issues

1. **God Class Anti-Pattern**: Single 620-line class handling 8+ distinct responsibilities
2. **Tight Coupling**: Direct dependency on `bot` object, breaking dependency injection principles
3. **Mixed Abstraction Levels**: Low-level dict manipulations mixed with high-level business logic
4. **Violation of SRP**: Position management, order execution, settlement, display, and strategy attribution in one class
5. **Duplicated Logic**: Repeated dict/object handling patterns throughout
6. **Hard-coded Business Rules**: Strategy attribution logic embedded in rebalancer

### Code Quality Issues

1. **Type Safety Violations**: Liberal use of `Any` and dynamic attribute access
2. **Error Handling Inconsistency**: Mix of exceptions, logging, and silent failures
3. **Magic Numbers**: Hardcoded thresholds (0.01, 0.95, 10.0) without configuration
4. **Display Logic Pollution**: Rich console calls mixed with business logic
5. **Settlement Logic**: Manual order waiting instead of using proper order management

## 🏗️ New Modular Architecture

### Domain Layer (Pure Business Logic)

```
the_alchemiser/domain/portfolio/
├── rebalancing/
│   ├── __init__.py
│   ├── rebalance_plan.py          # RebalancePlan value object
│   ├── rebalance_calculator.py    # Pure calculation logic
│   └── rebalance_strategy.py      # Strategy interface
├── position/
│   ├── __init__.py
│   ├── position_delta.py          # PositionDelta value object
│   └── position_analyzer.py       # Position analysis logic
└── strategy_attribution/
    ├── __init__.py
    ├── attribution_engine.py      # Strategy attribution logic
    └── symbol_classifier.py       # Symbol-to-strategy mapping
```

### Application Layer (Orchestration)

```
the_alchemiser/application/portfolio_management/
├── __init__.py
├── portfolio_rebalancer.py        # New clean orchestrator (100 lines max)
├── rebalance_orchestrator.py      # Workflow coordination
├── position_reconciler.py         # Post-trade position validation
└── rebalance_execution_plan.py    # Execution plan coordination
```

### Services Layer (Enhanced Existing)

```
the_alchemiser/services/enhanced/
├── portfolio_service.py           # Portfolio state management
├── rebalancing_service.py          # Rebalancing operations
└── position_tracking_service.py   # Position state tracking
```

### Infrastructure Layer (External Concerns)

```
the_alchemiser/infrastructure/portfolio/
├── __init__.py
├── portfolio_display.py           # Rich console formatting
├── rebalance_reporter.py          # Execution reporting
└── position_formatter.py          # Position display logic
```

## 📋 Implementation Plan

### Phase 1: Extract Domain Models (Week 1)

#### 1.1 Create Value Objects

```python
# domain/portfolio/rebalancing/rebalance_plan.py
@dataclass(frozen=True)
class RebalancePlan:
    symbol: str
    current_weight: Decimal
    target_weight: Decimal
    weight_diff: Decimal
    target_value: Decimal
    current_value: Decimal
    trade_amount: Decimal
    needs_rebalance: bool
    
    @property
    def trade_direction(self) -> Literal["BUY", "SELL", "HOLD"]:
        if not self.needs_rebalance:
            return "HOLD"
        return "BUY" if self.trade_amount > 0 else "SELL"

# domain/portfolio/position/position_delta.py
@dataclass(frozen=True)
class PositionDelta:
    symbol: str
    current_qty: Decimal
    target_qty: Decimal
    delta: Decimal
    action: Literal["no_change", "sell_excess", "buy_more"]
    quantity: Decimal
    message: str
```

#### 1.2 Extract Pure Calculation Logic

```python
# domain/portfolio/rebalancing/rebalance_calculator.py
class RebalanceCalculator:
    """Pure calculation logic for portfolio rebalancing."""
    
    def __init__(self, min_trade_threshold: Decimal = Decimal("0.01")):
        self.min_trade_threshold = min_trade_threshold
    
    def calculate_rebalance_plan(
        self,
        target_weights: Dict[str, Decimal],
        current_values: Dict[str, Decimal],
        total_portfolio_value: Decimal,
    ) -> Dict[str, RebalancePlan]:
        """Calculate comprehensive rebalancing plan using existing trading_math."""
        # Delegate to existing calculate_rebalance_amounts but return proper domain objects
        raw_plan = calculate_rebalance_amounts(
            {k: float(v) for k, v in target_weights.items()},
            {k: float(v) for k, v in current_values.items()},
            float(total_portfolio_value),
            float(self.min_trade_threshold)
        )
        
        return {
            symbol: RebalancePlan(
                symbol=symbol,
                current_weight=Decimal(str(data["current_weight"])),
                target_weight=Decimal(str(data["target_weight"])),
                weight_diff=Decimal(str(data["weight_diff"])),
                target_value=Decimal(str(data["target_value"])),
                current_value=Decimal(str(data["current_value"])),
                trade_amount=Decimal(str(data["trade_amount"])),
                needs_rebalance=data["needs_rebalance"]
            )
            for symbol, data in raw_plan.items()
        }

# domain/portfolio/position/position_analyzer.py
class PositionAnalyzer:
    """Pure position delta calculation logic."""
    
    def calculate_position_delta(
        self, symbol: str, current_qty: Decimal, target_qty: Decimal
    ) -> PositionDelta:
        """Calculate minimal order needed to reach target position."""
        delta = target_qty - current_qty
        
        if abs(delta) < Decimal("0.01"):
            return PositionDelta(
                symbol=symbol,
                current_qty=current_qty,
                target_qty=target_qty,
                delta=delta,
                action="no_change",
                quantity=Decimal("0"),
                message=f"No rebalancing needed for {symbol}: {current_qty} ≈ {target_qty}"
            )
        elif delta < 0:
            sell_qty = abs(delta).quantize(Decimal("0.000001"))
            return PositionDelta(
                symbol=symbol,
                current_qty=current_qty,
                target_qty=target_qty,
                delta=delta,
                action="sell_excess",
                quantity=sell_qty,
                message=f"Rebalancing {symbol}: selling {sell_qty} shares"
            )
        else:
            buy_qty = delta.quantize(Decimal("0.000001"))
            return PositionDelta(
                symbol=symbol,
                current_qty=current_qty,
                target_qty=target_qty,
                delta=delta,
                action="buy_more",
                quantity=buy_qty,
                message=f"Rebalancing {symbol}: buying {buy_qty} shares"
            )
```

### Phase 2: Extract Strategy Attribution (Week 1)

#### 2.1 Create Strategy Attribution Engine

```python
# domain/portfolio/strategy_attribution/attribution_engine.py
from the_alchemiser.domain.registry import StrategyType

class StrategyAttributionEngine:
    """Determines which strategy is responsible for each symbol."""
    
    def __init__(self, symbol_classifier: SymbolClassifier):
        self._classifier = symbol_classifier
    
    def get_primary_strategy(
        self,
        symbol: str,
        strategy_attribution: Optional[Dict[str, List[StrategyType]]] = None
    ) -> StrategyType:
        """Determine the primary strategy responsible for a symbol."""
        if strategy_attribution and symbol in strategy_attribution:
            strategies = strategy_attribution[symbol]
            if strategies:
                return strategies[0]
        
        return self._classifier.classify_symbol(symbol)

# domain/portfolio/strategy_attribution/symbol_classifier.py
class SymbolClassifier:
    """Classifies symbols to their primary strategy."""
    
    NUCLEAR_SYMBOLS = frozenset([
        "SMR", "LEU", "OKLO", "NLR", "BWXT", "PSQ", "SQQQ", "UUP", "UVXY", "BTAL"
    ])
    
    TECL_SYMBOLS = frozenset([
        "TECL", "TQQQ", "UPRO", "BIL", "QQQ"
    ])
    
    def classify_symbol(self, symbol: str) -> StrategyType:
        """Classify symbol to its primary strategy."""
        if symbol in self.NUCLEAR_SYMBOLS:
            return StrategyType.NUCLEAR
        elif symbol in self.TECL_SYMBOLS:
            return StrategyType.TECL
        else:
            return StrategyType.NUCLEAR  # Default fallback
```

### Phase 3: Create Application Orchestrator (Week 2)

#### 3.1 Clean Portfolio Rebalancer

```python
# application/portfolio_management/portfolio_rebalancer.py
class PortfolioRebalancer:
    """Clean orchestrator for portfolio rebalancing using dependency injection."""
    
    def __init__(
        self,
        rebalance_calculator: RebalanceCalculator,
        attribution_engine: StrategyAttributionEngine,
        position_analyzer: PositionAnalyzer,
        trading_service: TradingServiceManager,
        position_service: PositionService,
        account_service: AccountService,
        order_tracker: StrategyOrderTracker,
        portfolio_display: PortfolioDisplay,
        error_handler: TradingSystemErrorHandler,
    ):
        self._rebalance_calculator = rebalance_calculator
        self._attribution_engine = attribution_engine
        self._position_analyzer = position_analyzer
        self._trading_service = trading_service
        self._position_service = position_service
        self._account_service = account_service
        self._order_tracker = order_tracker
        self._portfolio_display = portfolio_display
        self._error_handler = error_handler
    
    def rebalance_portfolio(
        self,
        target_portfolio: Dict[str, Decimal],
        strategy_attribution: Optional[Dict[str, List[StrategyType]]] = None,
    ) -> List[OrderDetails]:
        """Main rebalancing workflow with clean separation of concerns."""
        try:
            # 1. Get current state
            account_info = self._account_service.get_account_info()
            current_positions = self._position_service.get_positions_dict()
            portfolio_value = account_info.portfolio_value
            
            # 2. Calculate rebalancing plan
            current_values = self._extract_position_values(current_positions)
            rebalance_plan = self._rebalance_calculator.calculate_rebalance_plan(
                target_portfolio, current_values, portfolio_value
            )
            
            # 3. Execute sell orders first
            sell_orders = self._execute_sell_orders(rebalance_plan, strategy_attribution)
            
            # 4. Wait for settlement and refresh state
            self._wait_for_settlement(sell_orders)
            account_info = self._account_service.get_account_info()
            
            # 5. Execute buy orders
            buy_orders = self._execute_buy_orders(rebalance_plan, strategy_attribution, account_info)
            
            # 6. Display results
            self._portfolio_display.show_rebalancing_summary(
                target_portfolio, account_info, self._position_service.get_positions()
            )
            
            return sell_orders + buy_orders
            
        except Exception as e:
            self._error_handler.handle_error(
                error=e,
                component="PortfolioRebalancer.rebalance_portfolio",
                context="portfolio_rebalancing",
                additional_data={"target_portfolio": target_portfolio}
            )
            raise PortfolioRebalancingError(f"Portfolio rebalancing failed: {e}") from e
```

#### 3.2 Create Execution Coordinators

```python
# application/portfolio_management/rebalance_orchestrator.py
class RebalanceOrchestrator:
    """Coordinates the sell-then-buy rebalancing workflow."""
    
    def execute_sell_phase(
        self, rebalance_plan: Dict[str, RebalancePlan], ...
    ) -> List[OrderDetails]:
        """Execute all sell orders including liquidations."""
        
    def execute_buy_phase(
        self, rebalance_plan: Dict[str, RebalancePlan], ...
    ) -> List[OrderDetails]:
        """Execute all buy orders with buying power management."""

# application/portfolio_management/position_reconciler.py
class PositionReconciler:
    """Handles post-trade position validation and reconciliation."""
    
    def reconcile_after_orders(self, executed_orders: List[OrderDetails]) -> bool:
        """Validate positions match expected state after order execution."""
```

### Phase 4: Extract Infrastructure Concerns (Week 2)

#### 4.1 Display Logic Separation

```python
# infrastructure/portfolio/portfolio_display.py
class PortfolioDisplay:
    """Handles all Rich console display logic for portfolio operations."""
    
    def show_liquidation_notice(self, symbol: str, reason: str) -> None:
        """Display liquidation notice with proper formatting."""
        console = Console()
        console.print(f"[yellow]Liquidating {symbol} ({reason})[/yellow]")
    
    def show_rebalancing_action(self, delta: PositionDelta) -> None:
        """Display rebalancing action with color coding."""
        console = Console()
        console.print(f"[cyan]{delta.message}[/cyan]")
    
    def show_buy_order_details(self, symbol: str, amount: Decimal, bid: Decimal, ask: Decimal) -> None:
        """Display buy order with bid/ask spread information."""
        console = Console()
        if bid > 0 and ask > 0:
            console.print(f"[green]Buying {symbol}: ${amount:.2f} (bid=${bid:.2f}, ask=${ask:.2f})[/green]")
        else:
            console.print(f"[green]Buying {symbol}: ${amount:.2f}[/green]")
```

### Phase 5: Enhanced Services Integration (Week 3)

#### 5.1 Create Portfolio Service

```python
# services/enhanced/portfolio_service.py
class PortfolioService:
    """High-level portfolio management operations."""
    
    def __init__(
        self,
        trading_service: TradingServiceManager,
        position_service: PositionService,
        account_service: AccountService,
    ):
        self._trading_service = trading_service
        self._position_service = position_service
        self._account_service = account_service
    
    def get_portfolio_state(self) -> PortfolioState:
        """Get complete portfolio state as a domain object."""
        
    def execute_rebalancing_trades(
        self, 
        sell_plans: List[RebalancePlan],
        buy_plans: List[RebalancePlan],
    ) -> RebalancingResult:
        """Execute rebalancing trades using existing TradingServiceManager."""
```

### Phase 6: Configuration and Error Handling (Week 3)

#### 6.1 Externalize Configuration

```python
# infrastructure/config/rebalancing_config.py
@dataclass
class RebalancingConfig:
    min_trade_threshold: Decimal = Decimal("0.01")
    cash_reserve_ratio: Decimal = Decimal("0.05")  # 95% usage instead of hardcoded
    minimum_buying_power: Decimal = Decimal("10.00")
    position_precision: int = 6
    settlement_timeout_seconds: int = 30

# Load from environment or settings
class RebalancingConfigLoader:
    @staticmethod
    def load_from_settings(settings: Settings) -> RebalancingConfig:
        return RebalancingConfig(
            min_trade_threshold=Decimal(str(settings.rebalancing.min_trade_threshold)),
            cash_reserve_ratio=Decimal(str(settings.rebalancing.cash_reserve_ratio)),
            # ... other config values
        )
```

## 🔄 Parallel Development & Safe Migration Strategy

### Phase 0: Preparation (Day 1-2)

1. **Create feature branch** for modernization work
2. **Add comprehensive integration tests** for existing portfolio rebalancer
3. **Document current behavior** with detailed test scenarios
4. **Set up parallel testing infrastructure**

### Phase 1: Foundation - Build Alongside (Week 1)

1. **Create new directory structure** without touching existing files:

   ```
   the_alchemiser/domain/portfolio/         # NEW - parallel to existing
   the_alchemiser/application/portfolio_management/  # NEW - parallel to existing
   ```

2. **Extract domain models** (RebalancePlan, PositionDelta) - pure value objects
3. **Extract pure calculation logic** (RebalanceCalculator, PositionAnalyzer)
4. **Extract strategy attribution** (StrategyAttributionEngine, SymbolClassifier)
5. **Add comprehensive unit tests** for all new domain logic
6. **Keep existing portfolio_rebalancer.py completely untouched**

### Phase 2: Application Layer - Build & Test (Week 2)

1. **Create new PortfolioRebalancer** with dependency injection in new location
2. **Build RebalanceOrchestrator** for workflow coordination
3. **Extract display logic** to infrastructure layer
4. **Create enhanced portfolio services**
5. **Add integration tests** that compare old vs new behavior
6. **Create adapter/wrapper** to test new system alongside old system

### Phase 3: Parallel Testing & Validation (Week 2-3)

1. **Create dual-mode testing harness**:

   ```python
   # tests/integration/test_portfolio_rebalancer_comparison.py
   class TestPortfolioRebalancerComparison:
       def test_rebalancing_behavior_identical(self):
           """Test that old and new rebalancers produce identical results."""
           # Run same inputs through both systems
           # Compare all outputs, orders, and side effects
   ```

2. **Add feature flag** for gradual rollout:

   ```python
   # infrastructure/config/feature_flags.py
   USE_NEW_PORTFOLIO_REBALANCER = env_bool("USE_NEW_PORTFOLIO_REBALANCER", False)
   ```

3. **Run extensive paper trading tests** with both systems
4. **Performance benchmark** old vs new implementation

### Phase 4: Gradual Migration (Week 3-4)

1. **Add adapter pattern** to maintain existing interface:

   ```python
   # application/portfolio_rebalancer/legacy_adapter.py
   class LegacyPortfolioRebalancerAdapter:
       """Adapter to maintain existing bot integration while using new system."""
       def __init__(self, bot: Any):
           self.bot = bot
           self._new_rebalancer = self._create_new_rebalancer()
       
       def rebalance_portfolio(self, target_portfolio, strategy_attribution=None):
           """Maintain exact same signature as existing system."""
           if settings.feature_flags.use_new_portfolio_rebalancer:
               return self._new_rebalancer.rebalance_portfolio(...)
           else:
               return self._old_rebalancer.rebalance_portfolio(...)
   ```

2. **Wire up dependency injection** without changing bot integration
3. **Enable feature flag** for paper trading first
4. **Monitor and validate** all paper trading behavior matches exactly

### Phase 5: Production Cutover (Week 4)

1. **Enable new system** for live trading after extensive validation
2. **Monitor closely** for any behavioral differences
3. **Keep old system** as immediate fallback for 1-2 weeks
4. **Document rollback procedure** if issues arise

### Phase 6: Cleanup (Week 5)

1. **Remove old monolithic file** only after new system proven stable
2. **Remove feature flags** and adapter code
3. **Update all documentation** and examples
4. **Clean up test infrastructure**

## 🛡️ Safety Mechanisms

### Behavioral Validation

```python
# tests/integration/rebalancer_behavior_validation.py
class RebalancerBehaviorValidator:
    """Ensures new implementation matches old behavior exactly."""
    
    def validate_portfolio_calculation(self, old_result, new_result):
        """Compare calculation results with tolerance for floating point."""
        assert len(old_result) == len(new_result)
        for symbol in old_result:
            assert abs(old_result[symbol] - new_result[symbol]) < 0.01
    
    def validate_order_sequence(self, old_orders, new_orders):
        """Ensure order sequences are equivalent."""
        # Compare order counts, symbols, quantities, timing
        
    def validate_settlement_behavior(self, old_settlement, new_settlement):
        """Ensure settlement logic produces same results."""
```

### Feature Flag Infrastructure

```python
# infrastructure/config/feature_flags.py
@dataclass
class FeatureFlags:
    use_new_portfolio_rebalancer: bool = False
    enable_rebalancer_comparison_logging: bool = True
    enable_rebalancer_performance_monitoring: bool = True
    
    @classmethod
    def from_environment(cls) -> 'FeatureFlags':
        return cls(
            use_new_portfolio_rebalancer=env_bool("USE_NEW_PORTFOLIO_REBALANCER", False),
            enable_rebalancer_comparison_logging=env_bool("ENABLE_REBALANCER_COMPARISON", True),
            enable_rebalancer_performance_monitoring=env_bool("ENABLE_REBALANCER_MONITORING", True),
        )
```

### Rollback Strategy

```python
# Emergency rollback procedure
def emergency_rollback_to_old_rebalancer():
    """Immediate rollback if new system shows issues."""
    # 1. Set feature flag to False
    # 2. Restart application
    # 3. Verify old system working
    # 4. Alert team of rollback
```

### Monitoring & Alerting

```python
# infrastructure/monitoring/rebalancer_monitor.py
class RebalancerMonitor:
    """Monitor rebalancer behavior during migration."""
    
    def log_execution_comparison(self, old_time, new_time, old_orders, new_orders):
        """Log performance and behavior differences."""
        
    def alert_on_behavioral_difference(self, difference_details):
        """Alert team if behavior diverges significantly."""
```

## 📊 Migration Risk Mitigation

### Zero-Downtime Strategy

- ✅ New system built completely in parallel
- ✅ Old system remains fully functional throughout development
- ✅ Feature flag allows instant rollback
- ✅ Adapter pattern maintains existing interfaces

### Validation Strategy

- ✅ Comprehensive integration tests comparing old vs new
- ✅ Paper trading validation for weeks before production
- ✅ Behavioral monitoring and alerting
- ✅ Performance benchmarking

### Recovery Strategy

- ✅ Old system preserved as immediate fallback
- ✅ Clear rollback procedures documented
- ✅ Monitoring alerts for any issues
- ✅ Gradual rollout with ability to pause/reverse

## 🎯 Expected Benefits

### Code Quality

- **Single Responsibility**: Each class has one clear purpose
- **Type Safety**: 100% mypy compliance with proper domain types
- **Testability**: Pure functions and dependency injection enable easy testing
- **Maintainability**: Small, focused classes easier to understand and modify

### Architecture

- **Loose Coupling**: Dependency injection removes tight coupling to `bot` object
- **High Cohesion**: Related functionality grouped in domain modules
- **Separation of Concerns**: Business logic, infrastructure, and display clearly separated
- **Extensibility**: Strategy attribution and display logic can be easily extended

### Performance

- **Reduced Complexity**: Simpler execution paths with clear data flow
- **Better Error Handling**: Consistent error management across all components
- **Improved Reliability**: Better settlement logic and order tracking

## 🔍 Current State Analysis

### Files to be Refactored

- `the_alchemiser/application/portfolio_rebalancer/portfolio_rebalancer.py` (620 lines) → Multiple focused classes

### Existing Assets to Leverage

- ✅ `the_alchemiser/domain/math/trading_math.py` - `calculate_rebalance_amounts()` function
- ✅ `the_alchemiser/services/enhanced/trading_service_manager.py` - Order execution facade
- ✅ `the_alchemiser/application/smart_execution.py` - Smart order placement
- ✅ `the_alchemiser/application/tracking/strategy_order_tracker.py` - Order tracking
- ✅ `the_alchemiser/services/error_handler.py` - Error handling infrastructure

### Dependencies to Update

- Bot integration points will need to use new PortfolioRebalancer interface
- CLI commands should use new services instead of direct bot methods
- Tests will need to be updated for new component structure

## 📊 Risk Assessment

### Low Risk

- Domain model extraction (pure value objects)
- Strategy attribution extraction (isolated logic)
- Display logic separation (no business impact)

### Medium Risk

- Application orchestrator creation (workflow changes)
- Service integration (dependency changes)
- Configuration externalization (behavior changes)

### High Risk

- Bot integration updates (main entry point changes)
- Order execution flow changes (trading logic)
- Settlement logic changes (timing-sensitive)

## ✅ Success Criteria

### Code Quality Metrics

- [ ] Reduce PortfolioRebalancer from 620 lines to <100 lines
- [ ] Achieve 100% mypy compliance across all new modules
- [ ] 90%+ test coverage for all domain logic
- [ ] Zero hardcoded magic numbers

### Architectural Goals

- [ ] Single responsibility for each class
- [ ] Dependency injection throughout
- [ ] Clear domain/application/infrastructure separation
- [ ] Reusable components for future portfolio features

### Functional Requirements

- [ ] Maintain exact same rebalancing behavior
- [ ] No regression in order execution performance
- [ ] Same error handling and logging quality
- [ ] Preserve all existing CLI functionality

This plan follows the DDD architecture principles outlined in the Copilot instructions while leveraging existing infrastructure like `TradingServiceManager`, `AlpacaManager`, and the smart execution engine. The result will be a modern, maintainable, and type-safe portfolio rebalancing system.
