# Stress Test Script

## Overview

The `stress_test.py` script performs comprehensive stress testing of The Alchemiser trading system by simulating all possible market conditions and scenarios.

## Purpose

This stress test:
- Runs the complete trading system with real Alpaca Paper API
- **Liquidation Mode (Default)**: Liquidates all positions between scenarios
- **Stateful Mode (NEW)**: Maintains portfolio state across scenarios to test rebalancing
- Mocks different market conditions (RSI values, prices, volatility)
- Iterates through all possible market scenarios
- Logs outcomes and detects edge cases
- Generates comprehensive reports with portfolio transition analysis

## Market Conditions Simulated

The script generates market conditions by combining:

### RSI Regimes
- **Oversold**: RSI 0-30
- **Neutral Low**: RSI 30-50
- **Neutral Mid**: RSI 45-55
- **Neutral High**: RSI 50-70
- **Overbought**: RSI 70-100
- **Extreme Overbought**: RSI 79-100 (critical threshold in strategies)

### Price Movement Scenarios
- **Crash**: -50% (high volatility)
- **Bear**: -20% (medium volatility)
- **Flat**: 0% (low volatility)
- **Bull**: +20% (medium volatility)
- **Boom**: +50% (high volatility)

### Edge Cases
- All symbols oversold + market crash (extreme bearish)
- All symbols overbought + market boom (extreme bullish)
- RSI at 79 threshold (decision boundary)
- RSI at 75 threshold (decision boundary)

## Usage

### Requirements

1. **Alpaca Paper API credentials** - The script automatically loads credentials using the system's configuration:
   - **Option A**: Use a `.env` file in the project root (recommended for development):
     ```bash
     # .env file
     ALPACA_KEY=your_paper_api_key
     ALPACA_SECRET=your_paper_secret_key
     ALPACA_ENDPOINT=https://paper-api.alpaca.markets
     ```
   - **Option B**: Set environment variables manually:
     ```bash
     export ALPACA_KEY=your_paper_api_key
     export ALPACA_SECRET=your_paper_secret_key
     export ALPACA_ENDPOINT=https://paper-api.alpaca.markets
     ```
   - **Option C**: Use Pydantic nested format:
     ```bash
     export ALPACA__KEY=your_paper_api_key
     export ALPACA__SECRET=your_paper_secret_key
     export ALPACA__ENDPOINT=https://paper-api.alpaca.markets
     ```

2. **No manual credential export needed** - The script uses the same credential system as the main trading application. You can also set dedicated stress-test credentials:
   - Optional dedicated variables (override at runtime):
     ```bash
     STRESS_TEST_KEY=your_paper_api_key
     STRESS_TEST_SECRET=your_paper_secret_key
     ```
     When present, the stress test automatically uses these and forces the endpoint to paper.

3. **Paper mode is always forced** - The stress test always forces the Alpaca endpoint to paper (`https://paper-api.alpaca.markets/v2`) to prevent accidental live testing.

4. The script uses real Alpaca Paper endpoints (no real money at risk)

### Running the Test

#### Makefile Commands (Recommended)

**Liquidation Mode (Default):**
```bash
make stress-test              # Full test (~34 scenarios)
make stress-test-quick        # Quick test (~14 scenarios)
```

**Stateful Mode (NEW - Maintains Portfolio):**
```bash
make stress-test-stateful       # Full stateful test (~34 scenarios)
make stress-test-stateful-quick # Quick stateful test (~14 scenarios)
```

**Dry Run:**
```bash
make stress-test-dry-run      # Show execution plan
```

#### Direct Poetry Commands

**Liquidation Mode (Default):**
```bash
poetry run python scripts/stress_test.py            # Full test
poetry run python scripts/stress_test.py --quick    # Quick test
```

**Stateful Mode:**
```bash
poetry run python scripts/stress_test.py --stateful            # Full stateful test
poetry run python scripts/stress_test.py --stateful --quick    # Quick stateful test
```

**Dry Run:**
```bash
poetry run python scripts/stress_test.py --dry-run
poetry run python scripts/stress_test.py --dry-run --quick
poetry run python scripts/stress_test.py --dry-run --stateful --quick
```

#### Test Your Setup First
```bash
poetry run python -c "from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys; print('✅ Credentials loaded successfully' if get_alpaca_keys()[0] else '❌ Credentials not found')"
```

This quick test verifies your credentials are properly configured before running the full stress test. If `STRESS_TEST_KEY/SECRET` are set, those will be used.

#### Custom Output File
```bash
poetry run python scripts/stress_test.py --output my_results.json
```

### Command Line Options

- `--quick` - Run subset of scenarios (~14 instead of ~34)
- `--dry-run` - Show execution plan without running trades
- `--stateful` - Maintain portfolio state across scenarios (no liquidation between scenarios)
- `--output FILE` - Specify output file (default: `stress_test_results.json`)

## Testing Modes

### Liquidation Mode (Default)

This is the original behavior that ensures clean state between scenarios:

1. **Initialize**: Load environment, check credentials
2. **Generate Scenarios**: Create all market condition combinations
3. **For Each Scenario**:
   - **Liquidate all positions** (via `AlpacaTradingService.close_all_positions()`)
   - Mock `IndicatorService` to return controlled values for the scenario
   - Run the full trading system (`main(["trade"])`)
   - Log results (success, trades executed, errors)
   - Wait 5 seconds to avoid rate limits
4. **Generate Report**: Compile statistics and save results

**Use When:**
- Testing individual scenarios in isolation
- Validating strategy logic for specific market conditions
- Debugging edge cases
- Ensuring deterministic test results

### Stateful Mode (NEW)

This mode maintains portfolio state across scenarios to test portfolio transitions:

1. **Initialize**: Load environment, check credentials
2. **Generate Scenarios**: Create all market condition combinations
3. **For Each Scenario**:
   - **Capture portfolio state** (positions, cash, allocations)
   - Mock `IndicatorService` to return controlled values for the scenario
   - Run the full trading system (`main(["trade"])`)
   - **Capture new portfolio state** after execution
   - **Calculate transition metrics** (rebalancing %, turnover cost, symbol changes)
   - Log results and portfolio evolution
   - Wait 5 seconds to avoid rate limits
4. **Generate Report**: Compile statistics, portfolio states, and transition analysis

**Use When:**
- Testing portfolio rebalancing behavior
- Analyzing transition costs and turnover
- Validating portfolio evolution across market conditions
- Understanding how strategies adapt to changing markets
- Stress-testing portfolio management logic

### Stateful Mode Metrics

The stateful mode tracks additional metrics:

**Portfolio State:**
- Positions (symbol → quantity)
- Market values (symbol → current value)
- Cash balance
- Total portfolio value
- Allocation percentages

**Transition Analysis:**
- Symbols added/removed/adjusted
- Rebalancing percentage (portfolio turnover)
- Estimated turnover costs
- Execution time
- Number of trades executed

## How It Works

### Market Condition Mocking

The script patches `IndicatorService` at the point of instantiation to return:
The script patches `IndicatorService` at the point of instantiation to return:
- **RSI values**: Within the scenario's RSI range, with deterministic variation per symbol
- **Prices**: Base price × scenario's price multiplier
- **Deterministic results**: Same symbol in same scenario always gets same values

This ensures:
- Reproducible test results
- Coverage of all logical branches in strategy DSL files
- Detection of edge cases and decision boundaries

## Architecture

### Modular Structure

The stress test has been refactored into a modular package for maintainability:

```
scripts/stress_test/
├── __init__.py
├── runner.py              # Main StressTestRunner orchestrator
├── models/
│   ├── __init__.py
│   ├── conditions.py      # MarketCondition dataclass
│   ├── results.py         # StressTestResult dataclass
│   └── portfolio_state.py # PortfolioState & PortfolioTransition
├── mocking/
│   ├── __init__.py
│   └── indicator_service.py  # MockIndicatorService
└── analysis/
    ├── __init__.py
    └── reporter.py        # StressTestReporter
```

**Key Components:**

- **`StressTestRunner`**: Orchestrates scenario execution, manages portfolio state tracking
- **`MockIndicatorService`**: Provides deterministic indicator values based on market conditions
- **`StressTestReporter`**: Generates comprehensive reports with optional stateful analysis
- **`PortfolioState`**: Captures portfolio composition at a point in time
- **`PortfolioTransition`**: Tracks changes between portfolio states

### Market Condition Mocking

The `MockIndicatorService` patches `IndicatorService` at instantiation to return:
- **RSI values**: Within the scenario's RSI range, with deterministic variation per symbol
- **Prices**: Base price × scenario's price multiplier
- **Deterministic results**: Same symbol in same scenario always gets same values

This ensures:
- Reproducible test results
- Coverage of all logical branches in strategy DSL files
- Detection of edge cases and decision boundaries

## Output

### Report Format

The stress test generates a JSON report with the following structure:

**Liquidation Mode:**
```json
{
  "summary": {
    "total_scenarios": 34,
    "successful": 32,
    "failed": 2,
    "success_rate": "94.12%",
    "total_trades_executed": 156,
    "total_execution_time_seconds": 3245.67,
    "average_time_per_scenario": 95.46,
    "mode": "liquidation"
  },
  "failures_by_type": {
    "ValueError": 1,
    "TimeoutError": 1
  },
  "edge_case_results": [...],
  "failed_scenarios": [...],
  "timestamp": "2025-01-15T10:30:00Z",
  "quick_mode": false,
  "dry_run": false
}
```

**Stateful Mode (Additional Fields):**
```json
{
  "summary": {
    ...
    "mode": "stateful"
  },
  "stateful_analysis": {
    "total_transitions": 33,
    "average_rebalance_percentage": 23.45,
    "total_turnover_cost": "1234.56",
    "symbols_added_total": 45,
    "symbols_removed_total": 38,
    "symbols_adjusted_total": 127,
    "portfolio_states_count": 34,
    "transitions": [
      {
        "from_scenario": "scenario_001",
        "to_scenario": "scenario_002",
        "trades_executed": 5,
        "symbols_added": ["NVDA", "MSFT"],
        "symbols_removed": ["SQQQ"],
        "symbols_adjusted": ["QQQ", "SPY"],
        "rebalance_percentage": 34.5,
        "turnover_cost": "456.78",
        "execution_time": 12.34
      },
      ...
    ]
  }
}
```

### Console Output

**Liquidation Mode:**
```
================================================================================
STRESS TEST SUMMARY
================================================================================

Mode:               liquidation
Total Scenarios:    34
Successful:         32
Failed:             2
Success Rate:       94.12%
Total Trades:       156
Total Time:         3245.67s
Avg Time/Scenario:  95.46s

Failures by Type:
  ValueError: 1
  TimeoutError: 1

Edge Case Results:
  ✓ edge_all_oversold_crash: 4 trades
  ✓ edge_all_overbought_boom: 6 trades
  ✓ edge_threshold_79: 3 trades
  ✓ edge_threshold_75: 2 trades

================================================================================
```

**Stateful Mode (Additional Output):**
```
================================================================================
STRESS TEST SUMMARY
================================================================================

Mode:               stateful
...

Stateful Mode Analysis:
  Total Transitions:        33
  Avg Rebalance %:          23.45%
  Total Turnover Cost:      1234.56
  Symbols Added (Total):    45
  Symbols Removed (Total):  38
  Symbols Adjusted (Total): 127

================================================================================
```

### JSON Report

The script generates a JSON report with:

```json
{
  "summary": {
    "total_scenarios": 34,
    "successful": 32,
    "failed": 2,
    "success_rate": "94.12%",
    "total_trades_executed": 156,
    "total_execution_time_seconds": 3845.67,
    "average_time_per_scenario": 113.11
  },
  "failures_by_type": {
    "TradingClientError": 1,
    "StrategyExecutionError": 1
  },
  "edge_case_results": [
    {
      "scenario_id": "edge_all_oversold_crash",
      "success": true,
      "trades": 5,
      "error": null
    },
    ...
  ],
  "failed_scenarios": [
    {
      "scenario_id": "scenario_023",
      "error_type": "TradingClientError",
      "error_message": "...",
      "timestamp": "2025-01-15T10:30:45.123456+00:00"
    }
  ]
}
```

### Console Output

The script prints:
- Progress during execution
- Summary statistics
- Edge case results
- Failed scenarios

## Testing the Script

Unit tests for the stress test are in `tests/test_stress_test.py`:

```bash
poetry run pytest tests/test_stress_test.py -v
```

Tests cover:
- Market condition generation
- Mock indicator service behavior
- Scenario planning
- Result aggregation

## Strategy Symbol Coverage

The script tests all **95+ symbols** used across strategy CLJ files:
- All `(asset ...)` declarations
- All symbols in `(rsi "SYMBOL" ...)` checks
- Coverage includes major ETFs (QQQ, SPY, TECL, TQQQ, etc.)
- Individual stocks (NVDA, MSFT, PLTR, etc.)
- Volatility instruments (UVXY, VIXY, VIXM)

## Expected Runtime

- **Dry run**: < 1 second
- **Quick mode**: 15-30 minutes (14 scenarios)
- **Full mode**: 1-2 hours (34 scenarios)

Runtime depends on:
- Alpaca API response times
- Strategy complexity
- Number of trades executed
- Market data fetching

## Troubleshooting

### "Missing required Alpaca credentials" or "ALPACA_KEY not set"
The script couldn't find your Alpaca Paper credentials. Try:
1. **Check your `.env` file** (recommended): Create/verify `.env` file in project root with:
   ```bash
   ALPACA_KEY=your_paper_api_key
   ALPACA_SECRET=your_paper_secret_key
   ALPACA_ENDPOINT=https://paper-api.alpaca.markets
   ```
2. **Set environment variables manually**:
   ```bash
   export ALPACA_KEY=your_paper_api_key
   export ALPACA_SECRET=your_paper_secret_key
   ```
3. **Check credential format**: Both `ALPACA_KEY` and `ALPACA__KEY` (nested) formats are supported

### "Failed to liquidate positions"
Check Alpaca API status and credentials. The script continues even if liquidation fails.

### Long execution time
This is expected. The script tests all possible market conditions comprehensively.
Use `--quick` for faster testing during development.

### Import errors
Make sure to run with `poetry run` to use the correct Python environment.

## Integration with CI/CD

The stress test can be integrated into CI/CD pipelines:

```bash
# In GitHub Actions or similar
poetry install
poetry run python scripts/stress_test.py --quick --output results/stress_test_results.json
```

Consider running:
- Quick mode in PR checks
- Full mode on nightly schedules
- Full mode before production deployments

## Future Enhancements

Potential improvements:
- [ ] Parallel scenario execution
- [ ] Custom scenario definitions via config file
- [ ] HTML report generation
- [ ] Performance benchmarking
- [ ] Historical comparison of results
- [ ] Slack/email notifications on completion
- [ ] Integration with monitoring systems
