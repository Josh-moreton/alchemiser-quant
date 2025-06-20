import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TradingStrategyBacktest:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=10000):
        """
        Initialize the backtesting system
        
        Parameters:
        start_date (str): Start date for backtesting (YYYY-MM-DD)
        end_date (str): End date for backtesting (YYYY-MM-DD), defaults to today
        initial_capital (float): Initial portfolio value
        """
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.portfolio = pd.DataFrame()
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data...")
        
        # Fetch TQQQ data (US ETF)
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        
        # Fetch LQQ3.L data (LSE ticker)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data. Please check ticker symbols and date range.")
        
        # Handle multi-level columns that yfinance sometimes returns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        if lqq3.columns.nlevels > 1:
            lqq3.columns = lqq3.columns.get_level_values(0)
        
        # Store data
        self.data['TQQQ'] = tqqq
        self.data['LQQ3'] = lqq3
        
        print(f"Data fetched successfully:")
        print(f"TQQQ: {len(tqqq)} days")
        print(f"LQQ3: {len(lqq3)} days")
        
        return self.data
    
    def calculate_signals(self):
        """Calculate trading signals based on TQQQ's 200-day SMA"""
        print("Calculating trading signals...")
        
        # Calculate 200-day SMA for TQQQ
        tqqq_data = self.data['TQQQ'].copy()
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Generate signals
        # 1 = Buy signal (TQQQ above 200 SMA)
        # 0 = Sell signal (TQQQ below 200 SMA)
        tqqq_data['Signal'] = np.where(tqqq_data['Close'] > tqqq_data['SMA_200'], 1, 0)
        
        # Calculate position changes
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        # Align dates with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Create a combined dataframe with proper alignment
        # First, get the overlapping date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter both datasets to the common date range
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge signals with LQQ3 data using outer join and forward fill
        signals_df = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'SMA_200', 'Signal', 'Position_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill signals for missing data (market holidays, etc.)
        signals_df['Signal'] = signals_df['Signal'].fillna(method='ffill')
        signals_df['Position_Change'] = signals_df['Position_Change'].fillna(0)
        signals_df['TQQQ_Close'] = signals_df['TQQQ_Close'].fillna(method='ffill')
        signals_df['SMA_200'] = signals_df['SMA_200'].fillna(method='ffill')
        
        # Drop rows where we don't have LQQ3 price data (can't trade without it)
        self.signals = signals_df.dropna(subset=['LQQ3_Close'])
        print(f"Signals calculated for {len(self.signals)} trading days")
        print(f"Date range: {self.signals.index.min()} to {self.signals.index.max()}")
        
        return self.signals
    
    def run_backtest(self):
        """Run the backtest simulation"""
        print("Running backtest...")
        
        if self.signals.empty:
            raise ValueError("No signals found. Run calculate_signals() first.")
        
        # Initialize portfolio tracking
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['Signal']
            position_change = row['Position_Change']
            
            # Portfolio value before any trades
            portfolio_value = cash + shares * lqq3_price
            
            # Execute trades based on signals
            if position_change == 1:  # Buy signal (TQQQ above 200 SMA)
                # Invest 100% of portfolio in LQQ3
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                    trade_amount = new_shares
                else:
                    trade_type = 'HOLD'
                    trade_amount = 0
                    
            elif position_change == -1:  # Sell signal (TQQQ below 200 SMA)
                # Sell 66% of portfolio, hold 34%
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
            
            # Calculate final portfolio value
            portfolio_value = cash + shares * lqq3_price
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'TQQQ_Price': row['TQQQ_Close'],
                'TQQQ_SMA200': row['SMA_200'],
                'Signal': signal,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount
            })
        
        self.portfolio = pd.DataFrame(portfolio_data)
        self.portfolio.set_index('Date', inplace=True)
        
        print(f"Backtest completed for {len(self.portfolio)} days")
        return self.portfolio
    
    def calculate_performance_metrics(self):
        """Calculate performance metrics"""
        if self.portfolio.empty:
            raise ValueError("No portfolio data. Run run_backtest() first.")
        
        # Calculate returns
        self.portfolio['Daily_Return'] = self.portfolio['Portfolio_Value'].pct_change()
        self.portfolio['Cumulative_Return'] = (self.portfolio['Portfolio_Value'] / self.initial_capital - 1) * 100
        
        # Buy and hold benchmark (LQQ3)
        self.portfolio['BuyHold_Value'] = (self.initial_capital * 
                                         self.portfolio['LQQ3_Price'] / 
                                         self.portfolio['LQQ3_Price'].iloc[0])
        self.portfolio['BuyHold_Return'] = (self.portfolio['BuyHold_Value'] / self.initial_capital - 1) * 100
        
        # Performance metrics
        total_return = (self.portfolio['Portfolio_Value'].iloc[-1] / self.initial_capital - 1) * 100
        buy_hold_return = (self.portfolio['BuyHold_Value'].iloc[-1] / self.initial_capital - 1) * 100
        
        # Calculate volatility (annualized)
        daily_returns = self.portfolio['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Maximum drawdown
        rolling_max = self.portfolio['Portfolio_Value'].expanding().max()
        drawdown = (self.portfolio['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Number of trades
        trades = self.portfolio[self.portfolio['Trade_Type'] != 'HOLD']
        num_trades = len(trades)
        
        metrics = {
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buy_hold_return, 2),
            'Excess Return (%)': round(total_return - buy_hold_return, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Final Portfolio Value': round(self.portfolio['Portfolio_Value'].iloc[-1], 2),
            'Initial Capital': self.initial_capital
        }
        
        return metrics
    
    def plot_results(self):
        """Create comprehensive plots of the backtest results"""
        if self.portfolio.empty:
            raise ValueError("No portfolio data. Run run_backtest() first.")
        
        # Ensure performance metrics are calculated (which creates BuyHold_Value)
        if 'BuyHold_Value' not in self.portfolio.columns:
            self.calculate_performance_metrics()
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Portfolio Value vs Buy & Hold', 'TQQQ Price vs 200 SMA', 
                          'LQQ3 Price', 'Portfolio Allocation'),
            vertical_spacing=0.08,
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}],
                   [{"secondary_y": False}],
                   [{"secondary_y": True}]]
        )
        
        # Plot 1: Portfolio value comparison
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=self.portfolio['Portfolio_Value'],
                      name='Strategy Portfolio', line=dict(color='blue', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=self.portfolio['BuyHold_Value'],
                      name='Buy & Hold LQQ3', line=dict(color='red', width=2)),
            row=1, col=1
        )
        
        # Plot 2: TQQQ vs SMA
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=self.portfolio['TQQQ_Price'],
                      name='TQQQ Price', line=dict(color='green')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=self.portfolio['TQQQ_SMA200'],
                      name='TQQQ 200 SMA', line=dict(color='orange')),
            row=2, col=1
        )
        
        # Plot 3: LQQ3 price
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=self.portfolio['LQQ3_Price'],
                      name='LQQ3 Price', line=dict(color='purple')),
            row=3, col=1
        )
        
        # Plot 4: Portfolio allocation
        portfolio_equity_value = self.portfolio['Shares'] * self.portfolio['LQQ3_Price']
        
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=self.portfolio['Cash'],
                      name='Cash', fill='tonexty', fillcolor='lightblue'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.portfolio.index, y=portfolio_equity_value,
                      name='LQQ3 Holdings', fill='tonexty', fillcolor='lightgreen'),
            row=4, col=1
        )
        
        # Update layout
        fig.update_layout(
            title='LQQ3 Trading Strategy Backtest Results',
            height=1200,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=4, col=1)
        fig.update_yaxes(title_text="Value (£)", row=1, col=1)
        fig.update_yaxes(title_text="Price ($)", row=2, col=1)
        fig.update_yaxes(title_text="Price (£)", row=3, col=1)
        fig.update_yaxes(title_text="Value (£)", row=4, col=1)
        
        fig.show()
        
        return fig
    
    def print_summary(self):
        """Print a summary of the backtest results"""
        metrics = self.calculate_performance_metrics()
        
        print("\n" + "="*60)
        print("TRADING STRATEGY BACKTEST SUMMARY")
        print("="*60)
        print(f"Strategy: Buy LQQ3 when TQQQ > 200 SMA, Sell 66% when TQQQ < 200 SMA")
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: £{metrics['Initial Capital']:,.2f}")
        print("-"*60)
        
        for key, value in metrics.items():
            if key not in ['Initial Capital']:
                print(f"{key:<25}: {value}")
        
        print("-"*60)
        
        # Trade summary
        trades = self.portfolio[self.portfolio['Trade_Type'] != 'HOLD']
        if not trades.empty:
            print("\nTRADE SUMMARY:")
            buy_trades = trades[trades['Trade_Type'] == 'BUY']
            sell_trades = trades[trades['Trade_Type'] == 'SELL']
            print(f"Buy signals: {len(buy_trades)}")
            print(f"Sell signals: {len(sell_trades)}")
            
            if len(trades) > 0:
                print(f"\nFirst trade: {trades.index[0].strftime('%Y-%m-%d')} ({trades['Trade_Type'].iloc[0]})")
                print(f"Last trade: {trades.index[-1].strftime('%Y-%m-%d')} ({trades['Trade_Type'].iloc[-1]})")
        
        print("="*60)

def main():
    """Main function to run the backtest"""
    # Initialize backtester
    backtester = TradingStrategyBacktest(
        start_date="2012-12-13",  # Full history since LQQ3 inception
        initial_capital=55000     # £10,000 starting capital
    )
    
    try:
        # Run the complete backtest
        backtester.fetch_data()
        backtester.calculate_signals()
        backtester.run_backtest()
        
        # Display results
        backtester.print_summary()
        backtester.plot_results()
        
        # Save results to CSV
        backtester.portfolio.to_csv('backtest_results.csv')
        print(f"\nDetailed results saved to 'backtest_results.csv'")
        
        return backtester
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        return None

if __name__ == "__main__":
    backtester = main()
