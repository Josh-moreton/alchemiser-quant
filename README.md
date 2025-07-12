# V1b Trading Strategy Alert Bot 🎯

This project converts your Composer.trade V1b symphony into a Python trading alert bot that generates buy/sell signals for manual trading in Robinhood or other brokers.

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure Email Alerts**
   Edit `alert_config.json` with your email settings:
   ```json
   {
     "email": {
       "sender_email": "your_email@gmail.com",
       "sender_password": "your_app_password",
       "recipient_emails": ["your_email@gmail.com"]
     }
   }
   ```

3. **Test the Bot**
   ```bash
   source venv/bin/activate
   python trading_alert_bot.py --mode once
   ```

4. **Run Dashboard**
   ```bash
   streamlit run dashboard.py
   ```

5. **Continuous Monitoring**
   ```bash
   python trading_alert_bot.py --mode continuous --interval 15
   ```

## 📊 Strategy Overview

The **V1b 15/15 BB + v4 Pops - K-1 Free** strategy implements a complex multi-factor approach:

### Key Components
- **Bond Market Regime**: RSI comparison between BIL vs IEF
- **Equity Momentum**: SPY RSI levels for market timing
- **Tech Sector Dynamics**: TQQQ, SOXL, TECL analysis
- **Volatility Assessment**: VIXY-based risk management
- **Mean Reversion**: Multi-timeframe RSI conditions

### Tracked Assets
- **Bull 3x ETFs**: SOXL, TECL, TQQQ, ERX
- **Bear 3x ETFs**: SOXS, SQQQ, TMV
- **Bonds**: BIL, IEF, TMF, BND, TLT
- **Indices**: SPY, QQQ, VTV, VOX
- **Volatility**: VIXY

## 🔧 Configuration

### Email Settings (Gmail)
1. Enable 2-Factor Authentication
2. Generate App Password: Google Account → Security → App passwords
3. Use app password (not regular password) in config

### Alert Settings
- `min_confidence`: Minimum confidence threshold (0.6 = 60%)
- `cooldown_minutes`: Prevent alert spam (30 minutes default)

## 📈 Usage Examples

### One-Time Analysis
```bash
python trading_alert_bot.py --mode once
```

### Continuous Monitoring (Every 15 Minutes)
```bash
python trading_alert_bot.py --mode continuous --interval 15
```

### Web Dashboard
```bash
streamlit run dashboard.py
```
Then open http://localhost:8501

## 📊 Sample Output

```
📊 Analysis: BUY SOXL at $28.45 (confidence: 75%)
🚨 ALERT SENT: BUY TECL at $52.30 (confidence: 80%)
📊 Analysis: HOLD BIL at $91.25 (confidence: 65%)
```

## 🎯 Alert Types

### Buy Signals
- **SOXL**: Bullish semiconductors (3x leveraged)
- **TECL**: Bullish technology (3x leveraged)
- **TQQQ**: Bullish Nasdaq (3x leveraged)
- **ERX**: Bullish energy (2x leveraged)

### Sell/Short Signals  
- **SOXS**: Bearish semiconductors (3x inverse)
- **SQQQ**: Bearish Nasdaq (3x inverse)
- **TMV**: Bearish long-term bonds (3x inverse)

### Safe Haven
- **BIL**: Treasury bills (cash equivalent)

## 📁 File Structure

```
├── trading_alert_bot.py     # Main bot logic
├── dashboard.py             # Streamlit web dashboard
├── alert_config.json        # Email and alert settings
├── requirements.txt         # Python dependencies
├── setup.sh                # Setup script
├── alerts.json             # Alert history log
├── trading_alerts.log      # Detailed logs
└── README.md               # This file
```

## 🔍 Strategy Logic Breakdown

### Level 1: Bond Market Filter
```python
if BIL_RSI(15) < IEF_RSI(15):
    # Risk-on environment
    if SPY_RSI(6) > 75:
        return "SOXS"  # Market overbought
    else:
        return evaluate_semiconductor_conditions()
else:
    # Main strategy tree
    return evaluate_complex_conditions()
```

### Level 2: Market Regime Detection
- **Oversold S&P** (RSI < 27): Bond vs stock strength analysis
- **Normal Markets**: Multi-factor QQQE, VTV, VOX analysis
- **High Volatility** (VIXY): Defensive positioning

### Level 3: Sector Rotation
- **Technology**: TECL vs SOXL based on RSI and momentum
- **Semiconductors**: SOXL vs SOXS based on volatility
- **Bonds**: BIL vs TMF based on drawdown analysis

## ⚠️ Risk Warnings

1. **Leveraged ETFs**: 2x-3x daily leverage = high volatility
2. **Backtesting**: Past performance ≠ future results
3. **Market Risk**: All investments carry risk of loss
4. **Technical Analysis**: Not guaranteed to predict markets

## 🤖 Automation Options

### Cron Job (Linux/Mac)
```bash
# Run every 15 minutes during market hours
*/15 9-16 * * 1-5 cd /path/to/bot && python trading_alert_bot.py --mode once
```

### Task Scheduler (Windows)
Create scheduled task to run bot during market hours

### Cloud Deployment
- **AWS Lambda**: Serverless execution
- **Google Cloud Functions**: Event-driven alerts
- **Heroku**: Simple cloud hosting

## 📞 Support

### Common Issues
1. **No email alerts**: Check Gmail app password setup
2. **Data errors**: Verify internet connection and Yahoo Finance access
3. **Import errors**: Run `pip install -r requirements.txt`

### Log Files
- `trading_alerts.log`: Detailed execution logs
- `alerts.json`: Historical alert data

## 📜 Disclaimer

**This software is for educational purposes only. Trading involves risk of financial loss. Always:**

- Do your own research
- Start with paper trading
- Never risk more than you can afford to lose
- Consider consulting a financial advisor

**The authors are not responsible for any trading losses.**

## 🔄 Updates

The bot automatically fetches current market data but strategy logic remains static. Monitor performance and consider:

- Adjusting confidence thresholds
- Modifying alert frequency
- Adding new indicators
- Backtesting parameter changes

---

**Happy Trading!** 📈🎯🚀
