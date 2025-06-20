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

class AdvancedTradingStrategyBacktest:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=10000):
        """
        Advanced backtesting system with multiple signal generation methods
        """
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.portfolio = pd.DataFrame()
        self.strategy_name = ""
        
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
    
    def calculate_signals_basic_sma(self, sma_period=200):
        """Basic 200-day SMA strategy (original)"""
        self.strategy_name = f"Basic {sma_period}-day SMA"
        
        tqqq_data = self.data['TQQQ'].copy()
        tqqq_data['SMA'] = tqqq_data['Close'].rolling(window=sma_period).mean()
        tqqq_data['Signal'] = np.where(tqqq_data['Close'] > tqqq_data['SMA'], 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_sma_with_buffer(self, sma_period=200, buffer_pct=2.0):
        """SMA with buffer zones to reduce whipsaws"""
        self.strategy_name = f"{sma_period}-day SMA with {buffer_pct}% buffer"
        
        tqqq_data = self.data['TQQQ'].copy()
        tqqq_data['SMA'] = tqqq_data['Close'].rolling(window=sma_period).mean()
        
        # Create upper and lower bands
        tqqq_data['Upper_Band'] = tqqq_data['SMA'] * (1 + buffer_pct/100)
        tqqq_data['Lower_Band'] = tqqq_data['SMA'] * (1 - buffer_pct/100)
        
        # Generate signals with hysteresis
        tqqq_data['Signal'] = 0
        current_signal = 0
        
        for i in range(len(tqqq_data)):
            price = tqqq_data['Close'].iloc[i]
            upper = tqqq_data['Upper_Band'].iloc[i]
            lower = tqqq_data['Lower_Band'].iloc[i]
            
            if pd.notna(price) and pd.notna(upper) and pd.notna(lower):
                if price > upper:
                    current_signal = 1
                elif price < lower:
                    current_signal = 0
                # Else maintain current signal (hysteresis)
                
            tqqq_data['Signal'].iloc[i] = current_signal
        
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_dual_sma(self, fast_period=50, slow_period=200):
        """Dual SMA crossover with noise reduction"""
        self.strategy_name = f"Dual SMA ({fast_period}/{slow_period})"
        
        tqqq_data = self.data['TQQQ'].copy()
        tqqq_data['SMA_Fast'] = tqqq_data['Close'].rolling(window=fast_period).mean()
        tqqq_data['SMA_Slow'] = tqqq_data['Close'].rolling(window=slow_period).mean()
        
        # Signal when fast SMA crosses above slow SMA
        tqqq_data['Signal'] = np.where(tqqq_data['SMA_Fast'] > tqqq_data['SMA_Slow'], 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        tqqq_data['SMA'] = tqqq_data['SMA_Slow']  # For compatibility
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_ema_crossover(self, fast_period=50, slow_period=200):
        """EMA crossover - more responsive than SMA"""
        self.strategy_name = f"EMA Crossover ({fast_period}/{slow_period})"
        
        tqqq_data = self.data['TQQQ'].copy()
        tqqq_data['EMA_Fast'] = tqqq_data['Close'].ewm(span=fast_period).mean()
        tqqq_data['EMA_Slow'] = tqqq_data['Close'].ewm(span=slow_period).mean()
        
        tqqq_data['Signal'] = np.where(tqqq_data['EMA_Fast'] > tqqq_data['EMA_Slow'], 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        tqqq_data['SMA'] = tqqq_data['EMA_Slow']  # For compatibility
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_macd(self, fast=12, slow=26, signal=9):
        """MACD-based signals"""
        self.strategy_name = f"MACD ({fast}/{slow}/{signal})"
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD
        ema_fast = tqqq_data['Close'].ewm(span=fast).mean()
        ema_slow = tqqq_data['Close'].ewm(span=slow).mean()
        tqqq_data['MACD'] = ema_fast - ema_slow
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=signal).mean()
        tqqq_data['MACD_Histogram'] = tqqq_data['MACD'] - tqqq_data['MACD_Signal']
        
        # Generate signals when MACD crosses above signal line
        tqqq_data['Signal'] = np.where(tqqq_data['MACD'] > tqqq_data['MACD_Signal'], 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        tqqq_data['SMA'] = tqqq_data['Close'].rolling(window=200).mean()  # For plotting
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_rsi_mean_reversion(self, rsi_period=14, rsi_oversold=30, rsi_overbought=70):
        """RSI-based mean reversion with SMA trend filter"""
        self.strategy_name = f"RSI Mean Reversion (RSI {rsi_period}, {rsi_oversold}/{rsi_overbought})"
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate RSI
        delta = tqqq_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        tqqq_data['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate 200-day SMA for trend filter
        tqqq_data['SMA'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Only buy when RSI is oversold AND price is above 200 SMA
        # Sell when RSI is overbought OR price is below 200 SMA
        tqqq_data['Signal'] = np.where(
            (tqqq_data['RSI'] > rsi_oversold) & (tqqq_data['Close'] > tqqq_data['SMA']), 1, 0
        )
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_bollinger_bands(self, period=20, std_dev=2):
        """Bollinger Bands with trend filter"""
        self.strategy_name = f"Bollinger Bands ({period}, {std_dev}σ)"
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate Bollinger Bands
        tqqq_data['BB_Middle'] = tqqq_data['Close'].rolling(window=period).mean()
        bb_std = tqqq_data['Close'].rolling(window=period).std()
        tqqq_data['BB_Upper'] = tqqq_data['BB_Middle'] + (bb_std * std_dev)
        tqqq_data['BB_Lower'] = tqqq_data['BB_Middle'] - (bb_std * std_dev)
        
        # Long-term trend filter
        tqqq_data['SMA'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Buy when price touches lower band and is above 200 SMA
        # Sell when price touches upper band or falls below 200 SMA
        tqqq_data['Signal'] = np.where(
            (tqqq_data['Close'] > tqqq_data['BB_Lower']) & (tqqq_data['Close'] > tqqq_data['SMA']), 1, 0
        )
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._create_signals_dataframe(tqqq_data)
    
    def calculate_signals_trend_following_combo(self):
        """Combination of multiple trend-following indicators"""
        self.strategy_name = "Multi-Indicator Trend Following"
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # 1. Multiple SMAs
        tqqq_data['SMA_50'] = tqqq_data['Close'].rolling(window=50).mean()
        tqqq_data['SMA_100'] = tqqq_data['Close'].rolling(window=100).mean()
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # 2. MACD
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        
        # 3. Price momentum
        momentum_20 = tqqq_data['Close'] / tqqq_data['Close'].shift(20)
        
        # Scoring system (0-4 points)
        score = 0
        score += np.where(tqqq_data['Close'] > tqqq_data['SMA_50'], 1, 0)
        score += np.where(tqqq_data['SMA_50'] > tqqq_data['SMA_100'], 1, 0)
        score += np.where(tqqq_data['SMA_100'] > tqqq_data['SMA_200'], 1, 0)
        score += np.where(macd > macd_signal, 1, 0)
        
        # Signal when 3 or more indicators are bullish
        tqqq_data['Signal'] = np.where(score >= 3, 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        tqqq_data['SMA'] = tqqq_data['SMA_200']  # For plotting
        
        return self._create_signals_dataframe(tqqq_data)
    
    def _create_signals_dataframe(self, tqqq_data):
        """Helper method to create aligned signals dataframe"""
        # Align dates with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Create a combined dataframe with proper alignment
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter both datasets to the common date range
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge signals with LQQ3 data
        signals_df = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'SMA', 'Signal', 'Position_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill signals for missing data
        signals_df['Signal'] = signals_df['Signal'].fillna(method='ffill')
        signals_df['Position_Change'] = signals_df['Position_Change'].fillna(0)
        signals_df['TQQQ_Close'] = signals_df['TQQQ_Close'].fillna(method='ffill')
        signals_df['SMA'] = signals_df['SMA'].fillna(method='ffill')
        
        # Drop rows where we don't have LQQ3 price data
        self.signals = signals_df.dropna(subset=['LQQ3_Close'])
        print(f"Signals calculated for {len(self.signals)} trading days using {self.strategy_name}")
        
        return self.signals
    
    def run_backtest(self):
        """Run the backtest simulation (same logic as original)"""
        print(f"Running backtest for {self.strategy_name}...")
        
        if self.signals.empty:
            raise ValueError("No signals found. Run a calculate_signals method first.")
        
        # Initialize portfolio tracking
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['Signal']
            position_change = row['Position_Change']
            
            # Execute trades based on signals
            if position_change == 1:  # Buy signal
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                    trade_amount = new_shares
                else:
                    trade_type = 'HOLD'
                    trade_amount = 0
                    
            elif position_change == -1:  # Sell signal
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
            
            # Calculate portfolio value
            portfolio_value = cash + shares * lqq3_price
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'TQQQ_Price': row['TQQQ_Close'],
                'TQQQ_SMA200': row['SMA'],
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
        
        # Buy and hold benchmark
        self.portfolio['BuyHold_Value'] = (self.initial_capital * 
                                         self.portfolio['LQQ3_Price'] / 
                                         self.portfolio['LQQ3_Price'].iloc[0])
        self.portfolio['BuyHold_Return'] = (self.portfolio['BuyHold_Value'] / self.initial_capital - 1) * 100
        
        # Performance metrics
        total_return = (self.portfolio['Portfolio_Value'].iloc[-1] / self.initial_capital - 1) * 100
        buy_hold_return = (self.portfolio['BuyHold_Value'].iloc[-1] / self.initial_capital - 1) * 100
        
        # Calculate volatility
        daily_returns = self.portfolio['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # Calculate Sharpe ratio
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Maximum drawdown
        rolling_max = self.portfolio['Portfolio_Value'].expanding().max()
        drawdown = (self.portfolio['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Number of trades
        trades = self.portfolio[self.portfolio['Trade_Type'] != 'HOLD']
        num_trades = len(trades)
        
        metrics = {
            'Strategy': self.strategy_name,
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buy_hold_return, 2),
            'Excess Return (%)': round(total_return - buy_hold_return, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Final Portfolio Value': round(self.portfolio['Portfolio_Value'].iloc[-1], 2)
        }
        
        return metrics

def test_multiple_strategies():
    """Test all signal generation methods and compare results"""
    print("="*80)
    print("TESTING MULTIPLE SIGNAL GENERATION STRATEGIES")
    print("="*80)
    
    results = []
    
    # List of strategies to test
    strategies = [
        ('Basic 200-day SMA', 'calculate_signals_basic_sma', {}),
        ('SMA with 2% buffer', 'calculate_signals_sma_with_buffer', {'buffer_pct': 2.0}),
        ('SMA with 3% buffer', 'calculate_signals_sma_with_buffer', {'buffer_pct': 3.0}),
        ('SMA with 5% buffer', 'calculate_signals_sma_with_buffer', {'buffer_pct': 5.0}),
        ('Dual SMA (50/200)', 'calculate_signals_dual_sma', {}),
        ('EMA Crossover (50/200)', 'calculate_signals_ema_crossover', {}),
        ('MACD', 'calculate_signals_macd', {}),
        ('Multi-Indicator', 'calculate_signals_trend_following_combo', {}),
    ]
    
    for strategy_name, method_name, params in strategies:
        try:
            print(f"\nTesting: {strategy_name}")
            print("-" * 50)
            
            # Create backtester instance
            backtester = AdvancedTradingStrategyBacktest(
                start_date="2012-12-13",
                initial_capital=10000
            )
            
            # Fetch data
            backtester.fetch_data()
            
            # Run specific strategy
            method = getattr(backtester, method_name)
            method(**params)
            
            # Run backtest
            backtester.run_backtest()
            
            # Calculate metrics
            metrics = backtester.calculate_performance_metrics()
            results.append(metrics)
            
            # Print summary
            print(f"Total Return: {metrics['Total Return (%)']}%")
            print(f"Excess Return: {metrics['Excess Return (%)']}%")
            print(f"Number of Trades: {metrics['Number of Trades']}")
            print(f"Sharpe Ratio: {metrics['Sharpe Ratio']}")
            print(f"Max Drawdown: {metrics['Max Drawdown (%)']}%")
            
        except Exception as e:
            print(f"Error testing {strategy_name}: {e}")
            continue
    
    # Create comparison table
    print("\n" + "="*80)
    print("STRATEGY COMPARISON SUMMARY")
    print("="*80)
    
    if results:
        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('Excess Return (%)', ascending=False)
        
        print(comparison_df.to_string(index=False))
        
        # Save to CSV
        comparison_df.to_csv('strategy_comparison.csv', index=False)
        print(f"\nDetailed comparison saved to 'strategy_comparison.csv'")
        
        # Identify best strategy
        best_strategy = comparison_df.iloc[0]
        print(f"\nBEST PERFORMING STRATEGY:")
        print(f"Strategy: {best_strategy['Strategy']}")
        print(f"Excess Return: {best_strategy['Excess Return (%)']}%")
        print(f"Total Return: {best_strategy['Total Return (%)']}%")
        print(f"Number of Trades: {best_strategy['Number of Trades']}")
        
        return comparison_df
    
    return None

if __name__ == "__main__":
    comparison_results = test_multiple_strategies()
