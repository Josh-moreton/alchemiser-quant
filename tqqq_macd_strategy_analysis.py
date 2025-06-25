import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

class TQQQMACDBacktest:
    def __init__(self, start_date="2010-01-01", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.portfolio = pd.DataFrame()

    def fetch_data(self):
        print("Fetching data...")
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data. Check ticker symbols and date range.")
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        if lqq3.columns.nlevels > 1:
            lqq3.columns = lqq3.columns.get_level_values(0)
        self.data['TQQQ'] = tqqq
        self.data['LQQ3'] = lqq3
        print(f"TQQQ: {len(tqqq)} days, LQQ3: {len(lqq3)} days")

    def calculate_signals(self):
        print("Calculating MACD signals...")
        tqqq = self.data['TQQQ'].copy()
        exp1 = tqqq['Close'].ewm(span=8).mean()
        exp2 = tqqq['Close'].ewm(span=20).mean()
        tqqq['MACD'] = exp1 - exp2
        tqqq['MACD_Signal'] = tqqq['MACD'].ewm(span=7).mean()
        tqqq['Signal'] = np.where(tqqq['MACD'] > tqqq['MACD_Signal'], 1, 0)
        tqqq['Position_Change'] = tqqq['Signal'].diff().fillna(0)
        lqq3 = self.data['LQQ3'].copy()
        start = max(lqq3.index.min(), tqqq.index.min())
        end = min(lqq3.index.max(), tqqq.index.max())
        lqq3 = lqq3.loc[start:end]
        tqqq = tqqq.loc[start:end]
        signals = pd.merge(
            lqq3[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq[['Close', 'MACD', 'MACD_Signal', 'Signal', 'Position_Change']].rename(columns={'Close': 'TQQQ_Close'}),
            left_index=True, right_index=True, how='outer'
        )
        signals['Signal'] = signals['Signal'].fillna(method='ffill')
        signals['Position_Change'] = signals['Position_Change'].fillna(0)
        signals['TQQQ_Close'] = signals['TQQQ_Close'].fillna(method='ffill')
        signals['MACD'] = signals['MACD'].fillna(method='ffill')
        signals['MACD_Signal'] = signals['MACD_Signal'].fillna(method='ffill')
        self.signals = signals.dropna(subset=['LQQ3_Close'])
        print(f"Signals calculated for {len(self.signals)} trading days")

    def run_backtest(self):
        print("Running MACD backtest...")
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        in_market_days = 0
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['Signal']
            position_change = row['Position_Change']
            if shares > 0:
                in_market_days += 1
            if position_change == 1:
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                    trade_amount = new_shares
                else:
                    trade_type = 'HOLD'
                    trade_amount = 0
            elif position_change == -1:
                if shares > 0:
                    shares_to_sell = shares * 0.66
                    cash += shares_to_sell * lqq3_price
                    shares -= shares_to_sell
                    trade_type = 'SELL'
                    trade_amount = shares_to_sell
                else:
                    trade_type = 'HOLD'
                    trade_amount = 0
            else:
                trade_type = 'HOLD'
                trade_amount = 0
            portfolio_value = cash + shares * lqq3_price
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'TQQQ_Price': row['TQQQ_Close'],
                'MACD': row['MACD'],
                'MACD_Signal': row['MACD_Signal'],
                'Signal': signal,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount
            })
        self.portfolio = pd.DataFrame(portfolio_data).set_index('Date')
        self.in_market_days = in_market_days
        print(f"Backtest completed for {len(self.portfolio)} days")

    def analyze_trades(self):
        trades = self.portfolio[self.portfolio['Trade_Type'] != 'HOLD']
        buy_trades = trades[trades['Trade_Type'] == 'BUY']
        sell_trades = trades[trades['Trade_Type'] == 'SELL']
        num_trades = len(trades)
        num_buys = len(buy_trades)
        num_sells = len(sell_trades)
        # Calculate trade outcomes
        winners = 0
        losers = 0
        returns = []
        last_buy_idx = None
        for idx, row in trades.iterrows():
            if row['Trade_Type'] == 'BUY':
                last_buy_idx = idx
                buy_price = row['LQQ3_Price']
            elif row['Trade_Type'] == 'SELL' and last_buy_idx is not None:
                sell_price = row['LQQ3_Price']
                ret = (sell_price - buy_price) / buy_price
                returns.append(ret)
                if ret > 0:
                    winners += 1
                else:
                    losers += 1
                last_buy_idx = None
        win_rate = (winners / (winners + losers) * 100) if (winners + losers) > 0 else 0
        avg_win = np.mean([r for r in returns if r > 0]) if winners > 0 else 0
        avg_loss = np.mean([r for r in returns if r <= 0]) if losers > 0 else 0
        time_in_market = self.in_market_days / len(self.portfolio) * 100
        print("\n===== MACD STRATEGY TRADE ANALYSIS =====")
        print(f"Total trades: {num_trades} (Buys: {num_buys}, Sells: {num_sells})")
        print(f"Winners: {winners}, Losers: {losers}, Win rate: {win_rate:.2f}%")
        print(f"Average win: {avg_win:.2%}, Average loss: {avg_loss:.2%}")
        print(f"Time in market: {time_in_market:.2f}%")
        print(f"First trade: {trades.index[0].strftime('%Y-%m-%d') if not trades.empty else 'N/A'}")
        print(f"Last trade: {trades.index[-1].strftime('%Y-%m-%d') if not trades.empty else 'N/A'}")
        print(f"Final portfolio value: £{self.portfolio['Portfolio_Value'].iloc[-1]:,.2f}")
        print(f"Initial capital: £{self.initial_capital:,.2f}")
        print(f"Total return: {(self.portfolio['Portfolio_Value'].iloc[-1] / self.initial_capital - 1) * 100:.2f}%")
        print("========================================\n")
        return {
            'num_trades': num_trades,
            'num_buys': num_buys,
            'num_sells': num_sells,
            'winners': winners,
            'losers': losers,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'time_in_market': time_in_market
        }

    def save_results(self, filename="tqqq_macd_backtest_results.csv"):
        self.portfolio.to_csv(filename)
        print(f"Detailed results saved to {filename}")

def main():
    backtest = TQQQMACDBacktest()
    backtest.fetch_data()
    backtest.calculate_signals()
    backtest.run_backtest()
    backtest.analyze_trades()
    backtest.save_results()

if __name__ == "__main__":
    main()
