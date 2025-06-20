#!/usr/bin/env python3
"""
Direct comparison: MACD Strategy vs 200-day SMA Strategy
Shows all key performance metrics side-by-side
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class StrategyComparison:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data...")
        
        # Fetch TQQQ data (US ETF)
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        
        # Fetch LQQ3.L data (LSE ticker)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data. Please check ticker symbols and date range.")
        
        # Handle multi-level columns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        if lqq3.columns.nlevels > 1:
            lqq3.columns = lqq3.columns.get_level_values(0)
        
        self.data['TQQQ'] = tqqq
        self.data['LQQ3'] = lqq3
        
        print(f"Data fetched: TQQQ {len(tqqq)} days, LQQ3 {len(lqq3)} days")
        return self.data
    
    def calculate_macd_signals(self):
        """Calculate MACD-based signals"""
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        
        # Generate signals when MACD crosses above/below signal line
        tqqq_data['Signal'] = np.where(tqqq_data['MACD'] > tqqq_data['MACD_Signal'], 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, 'MACD')
    
    def calculate_sma_signals(self):
        """Calculate 200-day SMA signals"""
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Generate signals when price crosses above/below SMA
        tqqq_data['Signal'] = np.where(tqqq_data['Close'] > tqqq_data['SMA_200'], 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, 'SMA')
    
    def _align_signals(self, tqqq_data, strategy_name):
        """Align TQQQ signals with LQQ3 data"""
        lqq3_data = self.data['LQQ3'].copy()
        
        # Find common date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter to common dates
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge data
        signals_df = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'Signal', 'Position_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        signals_df['Signal'] = signals_df['Signal'].fillna(method='ffill')
        signals_df['Position_Change'] = signals_df['Position_Change'].fillna(0)
        signals_df['TQQQ_Close'] = signals_df['TQQQ_Close'].fillna(method='ffill')
        
        # Drop rows without LQQ3 data
        signals_df = signals_df.dropna(subset=['LQQ3_Close'])
        
        print(f"{strategy_name} signals: {len(signals_df)} trading days")
        return signals_df
    
    def run_backtest(self, signals, strategy_name):
        """Run backtest for given signals"""
        print(f"Running {strategy_name} backtest...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['Signal']
            position_change = row['Position_Change']
            
            # Execute trades
            if position_change == 1:  # Buy signal
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                else:
                    trade_type = 'HOLD'
                    
            elif position_change == -1:  # Sell signal
                if shares > 0:
                    shares_to_sell = shares * 0.66  # Sell 66%
                    cash += shares_to_sell * lqq3_price
                    shares -= shares_to_sell
                    trade_type = 'SELL'
                else:
                    trade_type = 'HOLD'
            else:
                trade_type = 'HOLD'
            
            # Calculate portfolio value
            portfolio_value = cash + shares * lqq3_price
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'TQQQ_Price': row['TQQQ_Close'],
                'Signal': signal,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type
            })
        
        portfolio = pd.DataFrame(portfolio_data)
        portfolio.set_index('Date', inplace=True)
        
        print(f"{strategy_name} backtest completed: {len(portfolio)} days")
        return portfolio
    
    def calculate_metrics(self, portfolio, strategy_name):
        """Calculate performance metrics"""
        # Calculate returns
        portfolio['Daily_Return'] = portfolio['Portfolio_Value'].pct_change()
        
        # Buy and hold benchmark
        portfolio['BuyHold_Value'] = (self.initial_capital * 
                                    portfolio['LQQ3_Price'] / 
                                    portfolio['LQQ3_Price'].iloc[0])
        
        # Performance calculations
        final_value = portfolio['Portfolio_Value'].iloc[-1]
        initial_value = self.initial_capital
        buyhold_final = portfolio['BuyHold_Value'].iloc[-1]
        
        total_return = (final_value / initial_value - 1) * 100
        buyhold_return = (buyhold_final / initial_value - 1) * 100
        excess_return = total_return - buyhold_return
        
        # Risk metrics
        daily_returns = portfolio['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Maximum drawdown
        rolling_max = portfolio['Portfolio_Value'].expanding().max()
        drawdown = (portfolio['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Trading stats
        trades = portfolio[portfolio['Trade_Type'] != 'HOLD']
        num_trades = len(trades)
        
        # Time in market
        bullish_days = len(portfolio[portfolio['Signal'] == 1])
        total_days = len(portfolio)
        time_in_market = bullish_days / total_days * 100
        
        # Trading period
        years = (portfolio.index[-1] - portfolio.index[0]).days / 365.25
        trades_per_year = num_trades / years if years > 0 else 0
        
        return {
            'Strategy': strategy_name,
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buyhold_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Final Portfolio Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Trades per Year': round(trades_per_year, 1),
            'Time in Market (%)': round(time_in_market, 1),
            'Trading Period (Years)': round(years, 1)
        }

def main():
    """Main comparison function"""
    print("="*80)
    print("MACD vs 200-DAY SMA STRATEGY COMPARISON")
    print("="*80)
    print("Period: December 2012 - June 2025 (12.5 years)")
    print("Initial Capital: £10,000")
    print("Asset: LQQ3 (LSE) | Signal Source: TQQQ (NASDAQ)")
    print("-"*80)
    
    # Initialize comparison
    comparison = StrategyComparison(start_date="2012-12-13", initial_capital=55000)
    
    try:
        # Fetch data
        comparison.fetch_data()
        
        # Test MACD Strategy
        print(f"\n{'='*50}")
        print("TESTING MACD STRATEGY")
        print("="*50)
        macd_signals = comparison.calculate_macd_signals()
        macd_portfolio = comparison.run_backtest(macd_signals, "MACD")
        macd_metrics = comparison.calculate_metrics(macd_portfolio, "MACD (12/26/9)")
        
        # Test 200-day SMA Strategy
        print(f"\n{'='*50}")
        print("TESTING 200-DAY SMA STRATEGY")
        print("="*50)
        sma_signals = comparison.calculate_sma_signals()
        sma_portfolio = comparison.run_backtest(sma_signals, "200-day SMA")
        sma_metrics = comparison.calculate_metrics(sma_portfolio, "200-day SMA")
        
        # Display comparison results
        print(f"\n{'='*80}")
        print("PERFORMANCE COMPARISON RESULTS")
        print("="*80)
        
        # Create comparison table
        metrics_df = pd.DataFrame([macd_metrics, sma_metrics])
        
        # Print formatted comparison
        print(f"{'Metric':<30} {'MACD Strategy':<20} {'200-day SMA':<20} {'Difference':<15}")
        print("-"*85)
        
        key_metrics = [
            'Total Return (%)',
            'Excess Return (%)',
            'Final Portfolio Value (£)',
            'Max Drawdown (%)',
            'Sharpe Ratio',
            'Volatility (%)',
            'Number of Trades',
            'Trades per Year',
            'Time in Market (%)'
        ]
        
        for metric in key_metrics:
            macd_val = macd_metrics[metric]
            sma_val = sma_metrics[metric]
            
            if isinstance(macd_val, (int, float)) and isinstance(sma_val, (int, float)):
                diff = macd_val - sma_val
                diff_str = f"{diff:+.2f}" if metric != 'Number of Trades' else f"{diff:+.0f}"
            else:
                diff_str = "N/A"
            
            print(f"{metric:<30} {str(macd_val):<20} {str(sma_val):<20} {diff_str:<15}")
        
        # Key findings
        print(f"\n{'='*80}")
        print("KEY FINDINGS")
        print("="*80)
        
        excess_diff = macd_metrics['Excess Return (%)'] - sma_metrics['Excess Return (%)']
        drawdown_diff = macd_metrics['Max Drawdown (%)'] - sma_metrics['Max Drawdown (%)']
        
        print(f"💰 MACD outperformed by {excess_diff:+.2f}% excess return")
        print(f"📉 MACD had {drawdown_diff:+.2f}% {'better' if drawdown_diff > 0 else 'worse'} max drawdown")
        print(f"📊 MACD Sharpe ratio: {macd_metrics['Sharpe Ratio']} vs SMA: {sma_metrics['Sharpe Ratio']}")
        print(f"⚡ MACD traded {macd_metrics['Trades per Year']} times/year vs SMA: {sma_metrics['Trades per Year']}")
        print(f"⏰ MACD time in market: {macd_metrics['Time in Market (%)']}% vs SMA: {sma_metrics['Time in Market (%)']}%")
        
        # Winner declaration
        if macd_metrics['Total Return (%)'] > sma_metrics['Total Return (%)']:
            winner = "MACD Strategy"
            winner_return = macd_metrics['Total Return (%)']
        else:
            winner = "200-day SMA Strategy"
            winner_return = sma_metrics['Total Return (%)']
        
        print(f"\n🏆 WINNER: {winner} ({winner_return}% total return)")
        
        # Save detailed results
        macd_portfolio.to_csv('macd_vs_sma_macd_results.csv')
        sma_portfolio.to_csv('macd_vs_sma_sma_results.csv')
        metrics_df.to_csv('macd_vs_sma_comparison.csv', index=False)
        
        print(f"\n📁 Detailed results saved:")
        print(f"   • macd_vs_sma_macd_results.csv")
        print(f"   • macd_vs_sma_sma_results.csv")
        print(f"   • macd_vs_sma_comparison.csv")
        
        return metrics_df
        
    except Exception as e:
        print(f"Error running comparison: {e}")
        return None

if __name__ == "__main__":
    results = main()
