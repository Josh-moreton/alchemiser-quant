import logging
import numpy as np
import pandas as pd


class BullMarketStrategy:
    def __init__(self, get_nuclear_portfolio):
        self.get_nuclear_portfolio = get_nuclear_portfolio

    def recommend(self, indicators, market_data=None):
        nuclear_portfolio = self.get_nuclear_portfolio(indicators, market_data)
        if nuclear_portfolio:
            portfolio_stocks = list(nuclear_portfolio.keys())
            portfolio_desc = ", ".join([
                f"{s} ({nuclear_portfolio[s]['weight']:.1%})" for s in portfolio_stocks
            ])
            return 'NUCLEAR_PORTFOLIO', 'BUY', f"Bull market - Nuclear portfolio: {portfolio_desc}"
        return 'SMR', 'BUY', "Bull market - default nuclear energy play"

class BearMarketStrategy:
    def __init__(self, bear_subgroup_1, bear_subgroup_2, combine_bear_strategies_with_inverse_volatility):
        self.bear_subgroup_1 = bear_subgroup_1
        self.bear_subgroup_2 = bear_subgroup_2
        self.combine_bear_strategies_with_inverse_volatility = combine_bear_strategies_with_inverse_volatility

    def recommend(self, indicators):
        bear1_signal = self.bear_subgroup_1(indicators)
        bear2_signal = self.bear_subgroup_2(indicators)
        bear1_symbol = bear1_signal[0]
        bear2_symbol = bear2_signal[0]
        if bear1_symbol == bear2_symbol:
            return bear1_signal
        bear_portfolio = self.combine_bear_strategies_with_inverse_volatility(
            bear1_symbol, bear2_symbol, indicators
        )
        if bear_portfolio:
            portfolio_desc = ", ".join([
                f"{s} ({bear_portfolio[s]['weight']:.1%})" for s in bear_portfolio.keys()
            ])
            return 'BEAR_PORTFOLIO', 'BUY', f"Bear market portfolio: {portfolio_desc}"
        return bear1_signal

class OverboughtStrategy:
    def recommend(self, indicators):
        spy_rsi_10 = indicators['SPY']['rsi_10']
        if spy_rsi_10 > 81:
            return 'UVXY', 'BUY', "SPY extremely overbought (RSI > 81)"
        for symbol in ['IOO', 'TQQQ', 'VTV', 'XLF']:
            if symbol in indicators and indicators[symbol]['rsi_10'] > 81:
                return 'UVXY', 'BUY', f"{symbol} extremely overbought (RSI > 81)"
        # Return hedge portfolio instead of nuclear portfolio when market is overbought
        return 'UVXY_BTAL_PORTFOLIO', 'BUY', "IOO overbought, UVXY 75% + BTAL 25% allocation"

class SecondaryOverboughtStrategy:
    def recommend(self, indicators, overbought_symbol):
        if indicators[overbought_symbol]['rsi_10'] > 81:
            return 'UVXY', 'BUY', f"{overbought_symbol} extremely overbought"
        for symbol in ['TQQQ', 'VTV', 'XLF']:
            if symbol != overbought_symbol and symbol in indicators:
                if indicators[symbol]['rsi_10'] > 81:
                    return 'UVXY', 'BUY', f"{symbol} extremely overbought"
        # Return hedge portfolio instead of nuclear portfolio when secondary overbought
        return 'UVXY_BTAL_PORTFOLIO', 'BUY', f"{overbought_symbol} overbought, UVXY 75% + BTAL 25% allocation"

class VoxOverboughtStrategy:
    def recommend(self, indicators):
        if 'XLF' in indicators and indicators['XLF']['rsi_10'] > 81:
            return 'UVXY', 'BUY', "XLF extremely overbought"
        # Return hedge portfolio instead of nuclear portfolio when VOX overbought
        return 'UVXY_BTAL_PORTFOLIO', 'BUY', "VOX overbought, UVXY 75% + BTAL 25% allocation"

# Additional scenario classes can be added here as needed
