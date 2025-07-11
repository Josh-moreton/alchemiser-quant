# LQQ3 Trading Strategy Optimization Results

**Generated:** 2025-06-25 19:49:08

**Backtest Period:** 2010-12-13 to 2025-06-25

**Initial Capital:** £55,000

**Trading Asset:** LQQ3.L

**Objective:** Find strategies with drawdown better than -50%

---

## TQQQ as Signal Source

### 📊 Performance Summary

| Strategy | Total Return | Max Drawdown | Sharpe | Final Value |
|----------|--------------|--------------|--------|-------------|
| **MACD** | 19899.5% | -47.6% | 1.31 | £10,999,698 |
| **OR** | 14132.1% | -59.2% | 1.06 | £7,827,645 |
| **SMA** | 9461.7% | -43.3% | 1.08 | £5,258,944 |
| **VARIABLE** | 5849.2% | -52.4% | 1.04 | £3,272,065 |
| **WEIGHTED** | 4383.9% | -34.3% | 1.18 | £2,466,142 |

### 🏆 Winner: MACD

- **Total Return:** 19899.5%
- **Max Drawdown:** -47.6%
- **Sharpe Ratio:** 1.31
- **Final Value:** £10,999,698
- **Parameters:** fast=8, slow=20, signal=7

### 📋 Detailed Results

### MACD

✅ **Best Parameters:** fast=8, slow=20, signal=7

| Metric | Value |
|--------|-------|
| **Total Return** | 19899.45% |
| **Max Drawdown** | -47.61% |
| **Sharpe Ratio** | 1.31 |
| **Final Value** | £10,999,698.39 |

### SMA

✅ **Best Parameters:** period=150

| Metric | Value |
|--------|-------|
| **Total Return** | 9461.72% |
| **Max Drawdown** | -43.26% |
| **Sharpe Ratio** | 1.08 |
| **Final Value** | £5,258,944.06 |

### OR

✅ **Best Parameters:** Default

| Metric | Value |
|--------|-------|
| **Total Return** | 14132.08% |
| **Max Drawdown** | -59.16% |
| **Sharpe Ratio** | 1.06 |
| **Final Value** | £7,827,645.15 |

### AND

❌ **No results with drawdown better than -50%**
### WEIGHTED

✅ **Best Parameters:** MACD=0.4, SMA=0.6, threshold=0.6

| Metric | Value |
|--------|-------|
| **Total Return** | 4383.89% |
| **Max Drawdown** | -34.34% |
| **Sharpe Ratio** | 1.18 |
| **Final Value** | £2,466,141.90 |

### VARIABLE

✅ **Best Parameters:** Default

| Metric | Value |
|--------|-------|
| **Total Return** | 5849.21% |
| **Max Drawdown** | -52.35% |
| **Sharpe Ratio** | 1.04 |
| **Final Value** | £3,272,065.14 |

### MULTI

❌ **No results with drawdown better than -50%**
---

## QQQ as Signal Source

### 📊 Performance Summary

| Strategy | Total Return | Max Drawdown | Sharpe | Final Value |
|----------|--------------|--------------|--------|-------------|
| **MACD** | 19289.0% | -47.1% | 1.31 | £10,663,928 |
| **OR** | 13377.4% | -57.2% | 1.05 | £7,412,578 |
| **WEIGHTED** | 6264.1% | -42.4% | 1.22 | £3,500,228 |

### 🏆 Winner: MACD

- **Total Return:** 19289.0%
- **Max Drawdown:** -47.1%
- **Sharpe Ratio:** 1.31
- **Final Value:** £10,663,928
- **Parameters:** fast=8, slow=26, signal=7

### 📋 Detailed Results

### MACD

✅ **Best Parameters:** fast=8, slow=26, signal=7

| Metric | Value |
|--------|-------|
| **Total Return** | 19288.96% |
| **Max Drawdown** | -47.08% |
| **Sharpe Ratio** | 1.31 |
| **Final Value** | £10,663,928.12 |

### SMA

❌ **No results with drawdown better than -50%**
### OR

✅ **Best Parameters:** Default

| Metric | Value |
|--------|-------|
| **Total Return** | 13377.41% |
| **Max Drawdown** | -57.16% |
| **Sharpe Ratio** | 1.05 |
| **Final Value** | £7,412,578.15 |

### AND

❌ **No results with drawdown better than -50%**
### WEIGHTED

✅ **Best Parameters:** MACD=0.4, SMA=0.6, threshold=0.6

| Metric | Value |
|--------|-------|
| **Total Return** | 6264.05% |
| **Max Drawdown** | -42.40% |
| **Sharpe Ratio** | 1.22 |
| **Final Value** | £3,500,228.10 |

### VARIABLE

❌ **No results with drawdown better than -50%**
### MULTI

❌ **No results with drawdown better than -50%**
---

## 🎯 Overall Best Strategies

| Rank | Signal + Strategy | Total Return | Max Drawdown | Sharpe | Parameters |
|------|-------------------|--------------|--------------|--------|-----------|
| 1 | **TQQQ + MACD** | 19899.5% | -47.6% | 1.31 | fast=8, slow=20, signal=7 |
| 2 | **QQQ + MACD** | 19289.0% | -47.1% | 1.31 | fast=8, slow=26, signal=7 |
| 3 | **TQQQ + OR** | 14132.1% | -59.2% | 1.06 | Default |
| 4 | **QQQ + OR** | 13377.4% | -57.2% | 1.05 | Default |
| 5 | **TQQQ + SMA** | 9461.7% | -43.3% | 1.08 | period=150 |

