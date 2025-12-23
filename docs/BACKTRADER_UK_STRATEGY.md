# Backtrader UK TQQQ/SH Strategy

This backtrader script implements the "TQQQ or SH KMLM Phenomenon" trading strategy adapted for UK markets.

## Strategy Overview

The strategy uses RSI (Relative Strength Index) indicators across multiple instruments to dynamically switch between leveraged long and short positions:

- **LQQ3**: 3x Long Leveraged Nasdaq 100 ETF (UK equivalent of TQQQ)
- **XSPS**: Short S&P 500 ETF (UK equivalent of SH)

### Trading Logic

The strategy evaluates RSI indicators on a daily basis to determine position:

1. **Primary Decision**: Compare RSI(IEF, 20) vs RSI(PSQ, 20)
   - If IEF RSI > PSQ RSI:
     - Compare RSI(XLK, 10) vs RSI(KMLM, 10)
     - If XLK RSI > KMLM RSI: Hold **LQQ3** (leveraged long)
     - Else: Hold **XSPS** (short)
   
2. **Alternative Path**: If IEF RSI <= PSQ RSI:
   - If RSI(LQQ3, 10) < 31 (oversold): Hold **LQQ3**
   - Else: Hold **XSPS**

### Required Data Feeds

The strategy requires historical data for the following tickers:
- **IEF**: iShares 7-10 Year Treasury Bond ETF
- **PSQ**: ProShares Short QQQ
- **XLK**: Technology Select Sector SPDR Fund
- **KMLM**: KFA Mount Lucas Managed Futures Index Strategy ETF
- **LQQ3**: 3x Long Leveraged Nasdaq 100 ETF (UK)
- **XSPS**: Short S&P 500 ETF (UK)
- **DBMF**: iMGP DBi Managed Futures Strategy ETF

## Installation

The script requires backtrader, which has been added to the project dependencies:

```bash
# Install all dependencies
poetry install
```

## Data Preparation

Before running the backtest, you need historical data for all required tickers:

```bash
# Fetch all required symbols
python scripts/fetch_backtest_data.py --symbols IEF PSQ XLK KMLM LQQ3 XSPS DBMF

# Or use the existing data sync
make sync-data
```

## Usage

### Basic Usage

Run with default settings (last 365 days):

```bash
python scripts/backtrader_uk_tqqq_sh_strategy.py
```

### Custom Date Range

Specify start and end dates:

```bash
python scripts/backtrader_uk_tqqq_sh_strategy.py --start 2020-01-01 --end 2023-12-31
```

### Custom Initial Capital

Set a different starting capital:

```bash
python scripts/backtrader_uk_tqqq_sh_strategy.py --capital 50000
```

### Generate Plot

Create a visual chart of the backtest:

```bash
python scripts/backtrader_uk_tqqq_sh_strategy.py --plot
```

### Verbose Output

See detailed trade logs:

```bash
python scripts/backtrader_uk_tqqq_sh_strategy.py --verbose
```

### Combined Options

```bash
python scripts/backtrader_uk_tqqq_sh_strategy.py \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --capital 100000 \
  --commission 0.002 \
  --verbose \
  --plot
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--start` | 365 days ago | Start date (YYYY-MM-DD) |
| `--end` | Today | End date (YYYY-MM-DD) |
| `--capital` | 100000 | Initial capital |
| `--data-dir` | data/historical | Path to historical data directory |
| `--commission` | 0.001 | Commission rate (0.001 = 0.1%) |
| `--plot` | False | Generate plot of results |
| `--verbose` | False | Enable verbose output |

## Output

The script provides comprehensive backtest results including:

### Performance Metrics
- Final Portfolio Value
- Total Return (absolute and percentage)
- Sharpe Ratio
- Maximum Drawdown
- Average Annual Return

### Trade Statistics
- Total number of trades
- Winning trades
- Losing trades
- Win rate

### Example Output

```
======================================================================
BACKTRADER STRATEGY BACKTEST
======================================================================
Strategy:        TQQQ/SH KMLM Phenomenon (UK adapted)
Start Date:      2020-01-01
End Date:        2023-12-31
Initial Capital: $100,000.00
Commission:      0.10%
Data Directory:  data/historical
======================================================================
Starting Portfolio Value: $100,000.00

======================================================================
BACKTEST RESULTS
======================================================================
Final Portfolio Value: $145,234.56
Total Return:          +$45,234.56 (+45.23%)

Performance Metrics:
  Sharpe Ratio:        1.45
  Max Drawdown:        -18.34%
  Total Return:        45.23%
  Average Annual:      12.45%

Trade Statistics:
  Total Trades:        245
  Won:                 148
  Lost:                97
  Win Rate:            60.41%
======================================================================
```

## Strategy Files

Two versions of the strategy are available:

1. **Backtrader Script**: `scripts/backtrader_uk_tqqq_sh_strategy.py`
   - Standalone Python backtrader implementation
   - Full control over execution and analysis
   - Visual plotting capabilities

2. **DSL Strategy File**: `the_alchemiser/strategy_v2/strategies/tqqq_sh_kmlm_uk.clj`
   - Native Alchemiser DSL format
   - Can be used with the main portfolio backtest engine
   - Integrated with the Lambda-based production system

## Notes

### UK Ticker Substitutions

The original US strategy has been adapted with UK equivalents:

- **TQQQ** (ProShares UltraPro QQQ 3x) → **LQQ3** (3x Long Leveraged Nasdaq 100 ETF)
- **SH** (ProShares Short S&P500 -1x) → **XSPS** (Short S&P 500 ETF)

### Data Availability

Please note that UK ticker data (LQQ3, XSPS) may have limited history or availability compared to US tickers. If you encounter data issues:

1. Check if the tickers are available through your data provider
2. Consider using alternative UK-listed leveraged/inverse ETFs
3. Verify data quality and completeness before running backtests

### Limitations

- The backtrader implementation rebalances daily based on RSI signals
- Commission and slippage are modeled but may not reflect real-world execution
- Results are historical and do not guarantee future performance
- UK market hours and liquidity may differ from US markets

## Integration with Alchemiser

The DSL version (`tqqq_sh_kmlm_uk.clj`) can be integrated into the main Alchemiser system:

1. Add to portfolio configuration:
   ```json
   {
     "strategies": [
       {
         "name": "UK TQQQ/SH KMLM",
         "dsl_file": "tqqq_sh_kmlm_uk.clj",
         "weight": 0.2
       }
     ]
   }
   ```

2. Run with main backtest engine:
   ```bash
   python scripts/run_backtest.py --config your_portfolio_config.json
   ```

## Troubleshooting

### Missing Data Files

**Error**: `Data file not found for <ticker>`

**Solution**: Fetch the required data:
```bash
python scripts/fetch_backtest_data.py --symbols IEF PSQ XLK KMLM LQQ3 XSPS DBMF
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'backtrader'`

**Solution**: Install dependencies:
```bash
poetry install
```

### Empty DataFrame

**Error**: `No data for <ticker> in date range`

**Solution**: 
1. Check if data exists for the requested date range
2. Fetch more historical data
3. Adjust start/end dates to match available data

## Further Reading

- [Backtrader Documentation](https://www.backtrader.com/docu/)
- [RSI Indicator](https://www.investopedia.com/terms/r/rsi.asp)
- [Alchemiser Documentation](../README.md)

## License

MIT License - See repository root for details.
