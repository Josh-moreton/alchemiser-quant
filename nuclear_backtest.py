#!/usr/bin/env python3
"""
Nuclear Energy Strategy Backtesting Script
Compare our Python implementation with Composer.trade results
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import our Nuclear strategy
from nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators

class NuclearBacktester:
    """Backtest the Nuclear Energy strategy"""
    
    def __init__(self, start_date="2022-03-24", end_date=None):
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.strategy = NuclearStrategyEngine()
        self.indicators = TechnicalIndicators()
        
        # Trading costs
        self.commission_rate = 0.001  # 0.1% per trade
        self.initial_capital = 100000  # $100k starting capital
        
        print(f"Backtesting Nuclear Energy Strategy from {start_date} to {self.end_date}")
    
    def fetch_historical_data(self):
        """Fetch historical data for all symbols"""
        print("Fetching historical data...")
        
        # Calculate start date with buffer for indicators
        start_buffer = pd.to_datetime(self.start_date) - timedelta(days=300)
        
        historical_data = {}
        failed_symbols = []
        
        for symbol in self.strategy.all_symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_buffer, end=self.end_date)
                
                if not data.empty and len(data) > 200:  # Need enough data for 200-day MA
                    historical_data[symbol] = data
                    print(f"✓ {symbol}: {len(data)} days")
                else:
                    failed_symbols.append(symbol)
                    print(f"✗ {symbol}: insufficient data")
            except Exception as e:
                failed_symbols.append(symbol)
                print(f"✗ {symbol}: {e}")
        
        if failed_symbols:
            print(f"\nFailed to fetch data for: {failed_symbols}")
        
        return historical_data
    
    def calculate_daily_indicators(self, historical_data, date):
        """Calculate indicators for a specific date"""
        indicators = {}
        
        # Ensure date is timezone-aware if needed
        if isinstance(date, pd.Timestamp):
            date = date.tz_localize(None)  # Remove timezone to match data
        
        for symbol, df in historical_data.items():
            # Ensure dataframe index is timezone-naive
            if df.index.tz is not None:
                df = df.tz_localize(None)
            
            # Get data up to the current date
            data_slice = df[df.index <= date]
            
            if len(data_slice) < 200:  # Need minimum data for indicators
                continue
                
            close = data_slice['Close']
            
            # Calculate all indicators
            indicators[symbol] = {
                'rsi_10': self.safe_get_last_value(self.indicators.rsi(close, 10)),
                'rsi_20': self.safe_get_last_value(self.indicators.rsi(close, 20)),
                'ma_200': self.safe_get_last_value(self.indicators.moving_average(close, 200)),
                'ma_20': self.safe_get_last_value(self.indicators.moving_average(close, 20)),
                'ma_return_90': self.safe_get_last_value(self.indicators.moving_average_return(close, 90)),
                'cum_return_60': self.safe_get_last_value(self.indicators.cumulative_return(close, 60)),
                'current_price': float(close.iloc[-1]),
            }
        
        return indicators
    
    def safe_get_last_value(self, series):
        """Safely get the last value from a series"""
        try:
            if hasattr(series, 'iloc') and len(series) > 0:
                value = float(series.iloc[-1])
                return value if not pd.isna(value) else 50.0
            return 50.0
        except:
            return 50.0
    
    def run_backtest(self):
        """Run the complete backtest"""
        
        # Fetch data
        historical_data = self.fetch_historical_data()
        
        if not historical_data:
            print("No historical data available for backtesting")
            return None
        
        # Create date range for backtesting
        start_dt = pd.to_datetime(self.start_date)
        end_dt = pd.to_datetime(self.end_date)
        
        # Get business days only
        business_days = pd.bdate_range(start=start_dt, end=end_dt)
        
        # Initialize tracking variables
        results = []
        current_position = None
        current_shares = 0
        cash = self.initial_capital
        portfolio_value = self.initial_capital
        
        print(f"\nRunning backtest over {len(business_days)} trading days...")
        
        for i, date in enumerate(business_days):
            if i % 50 == 0:
                print(f"Progress: {i+1}/{len(business_days)} days ({100*(i+1)/len(business_days):.1f}%)")
            
            # Calculate indicators for this date
            indicators = self.calculate_daily_indicators(historical_data, date)
            
            if not indicators:
                continue
            
            # Get strategy recommendation
            try:
                symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators)
            except Exception as e:
                print(f"Strategy error on {date}: {e}")
                continue
            
            # Get current price for the recommended symbol
            if symbol not in historical_data:
                continue
                
            symbol_data = historical_data[symbol]
            price_data = symbol_data[symbol_data.index <= date]
            
            if price_data.empty:
                continue
                
            current_price = float(price_data['Close'].iloc[-1])
            
            # Execute trades
            if action == 'BUY' and symbol != current_position:
                # Close current position if any
                if current_position and current_shares > 0:
                    if current_position in historical_data:
                        old_price_data = historical_data[current_position]
                        old_price_slice = old_price_data[old_price_data.index <= date]
                        if not old_price_slice.empty:
                            old_price = float(old_price_slice['Close'].iloc[-1])
                            sale_value = current_shares * old_price
                            cash = sale_value * (1 - self.commission_rate)
                
                # Open new position
                current_shares = cash / current_price
                cash = 0
                current_position = symbol
                
                # Apply commission
                current_shares *= (1 - self.commission_rate)
            
            # Calculate portfolio value
            if current_position and current_shares > 0:
                portfolio_value = current_shares * current_price
            else:
                portfolio_value = cash
            
            # Record results
            results.append({
                'date': date,
                'symbol': symbol,
                'action': action,
                'reason': reason,
                'price': current_price,
                'position': current_position,
                'shares': current_shares,
                'cash': cash,
                'portfolio_value': portfolio_value,
                'return_pct': ((portfolio_value - self.initial_capital) / self.initial_capital) * 100
            })
        
        # Create results DataFrame
        df_results = pd.DataFrame(results)
        
        if df_results.empty:
            print("No backtest results generated")
            return None
        
        # Calculate performance metrics
        self.analyze_performance(df_results)
        
        return df_results
    
    def analyze_performance(self, df_results):
        """Analyze backtest performance"""
        print("\n" + "="*60)
        print("NUCLEAR ENERGY STRATEGY BACKTEST RESULTS")
        print("="*60)
        
        # Basic performance metrics
        initial_value = self.initial_capital
        final_value = df_results['portfolio_value'].iloc[-1]
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Time period
        start_date = df_results['date'].iloc[0]
        end_date = df_results['date'].iloc[-1]
        days = (end_date - start_date).days
        years = days / 365.25
        
        # Annualized return
        annualized_return = (final_value / initial_value) ** (1/years) - 1
        
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Duration: {days} days ({years:.1f} years)")
        print(f"Initial Capital: ${initial_value:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Annualized Return: {annualized_return:.2f}%")
        
        # Volatility and Sharpe ratio
        daily_returns = df_results['portfolio_value'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0  # Assuming 2% risk-free rate
        
        print(f"Annualized Volatility: {volatility:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        
        # Drawdown analysis
        running_max = df_results['portfolio_value'].expanding().max()
        drawdown = (df_results['portfolio_value'] - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        print(f"Maximum Drawdown: {max_drawdown:.2f}%")
        
        # Position analysis
        positions = df_results['position'].value_counts()
        print(f"\nPosition Distribution:")
        for symbol, count in positions.items():
            pct = (count / len(df_results)) * 100
            print(f"  {symbol}: {count} days ({pct:.1f}%)")
        
        # Compare to SPY (if available)
        self.compare_to_spy(df_results)
    
    def compare_to_spy(self, df_results):
        """Compare performance to SPY benchmark"""
        try:
            spy_ticker = yf.Ticker('SPY')
            spy_data = spy_ticker.history(start=self.start_date, end=self.end_date)
            
            if not spy_data.empty:
                spy_start = spy_data['Close'].iloc[0]
                spy_end = spy_data['Close'].iloc[-1]
                spy_return = ((spy_end - spy_start) / spy_start) * 100
                
                strategy_return = df_results['return_pct'].iloc[-1]
                outperformance = strategy_return - spy_return
                
                print(f"\nBenchmark Comparison (SPY):")
                print(f"SPY Return: {spy_return:.2f}%")
                print(f"Strategy Return: {strategy_return:.2f}%")
                print(f"Outperformance: {outperformance:.2f}%")
        except Exception as e:
            print(f"Could not compare to SPY: {e}")
    
    def plot_results(self, df_results):
        """Plot backtest results"""
        if df_results is None or df_results.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Portfolio value over time
        axes[0, 0].plot(df_results['date'], df_results['portfolio_value'])
        axes[0, 0].set_title('Portfolio Value Over Time')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Portfolio Value ($)')
        axes[0, 0].grid(True)
        
        # Returns over time
        axes[0, 1].plot(df_results['date'], df_results['return_pct'])
        axes[0, 1].set_title('Cumulative Returns (%)')
        axes[0, 1].set_xlabel('Date')
        axes[0, 1].set_ylabel('Return (%)')
        axes[0, 1].grid(True)
        
        # Position distribution
        positions = df_results['position'].value_counts()
        axes[1, 0].pie(positions.values, labels=positions.index, autopct='%1.1f%%')
        axes[1, 0].set_title('Position Distribution')
        
        # Drawdown
        running_max = df_results['portfolio_value'].expanding().max()
        drawdown = (df_results['portfolio_value'] - running_max) / running_max * 100
        axes[1, 1].fill_between(df_results['date'], drawdown, 0, alpha=0.3, color='red')
        axes[1, 1].set_title('Drawdown (%)')
        axes[1, 1].set_xlabel('Date')
        axes[1, 1].set_ylabel('Drawdown (%)')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig('nuclear_backtest_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"\nPlot saved as 'nuclear_backtest_results.png'")

def main():
    """Main backtesting function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backtest Nuclear Energy Strategy')
    parser.add_argument('--start', default='2022-03-24', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default=None, help='End date (YYYY-MM-DD)')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    
    args = parser.parse_args()
    
    # Create backtester
    backtester = NuclearBacktester(start_date=args.start, end_date=args.end)
    
    # Run backtest
    results = backtester.run_backtest()
    
    if results is not None:
        # Save results
        results.to_csv('nuclear_backtest_results.csv', index=False)
        print(f"\nResults saved to 'nuclear_backtest_results.csv'")
        
        # Generate plots if requested
        if args.plot:
            backtester.plot_results(results)
    else:
        print("Backtest failed to generate results")

if __name__ == "__main__":
    main()
