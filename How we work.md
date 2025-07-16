# How this bot should work

nuclear_trading_bot.py - this file should import indicators.py, access live market data, and generate the current trading signal based on the trading logic stored within it.

nuclear_signal_email.py - This should receive a trading signal from nuclear_trading_bot.py, and if the signal differed from yesterday, it should send an email using SMTP

alpaca_trader.py - This should receive a trading signal from nuclear_trading_bot.py, review the current signal against the current portfolio in the Alpaca account, work out what needs doing (buy, sell, rebalance) and place trades via the Alpaca API. It then should send an email with an update of its actions. (This could maybe be done by the emailing module?)

Tell me how far we deviate from the above, and what we need to do to reach it.
