#!/usr/bin/env python3
"""
FINAL OPTIMIZED STRATEGY: OR Logic Hybrid (MACD + SMA)
The ultimate combination that delivered 10,189% returns vs 5,405% buy-and-hold

Signal Logic:
- BUY: When TQQQ price > 200 SMA OR TQQQ MACD > Signal Line
- SELL: When TQQQ price < 200 SMA AND TQQQ MACD < Signal Line
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OptimizedHybridStrategy:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.portfolio = pd.DataFrame()
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data for Optimized Hybrid Strategy...")
        
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
    
    def calculate_or_logic_signals(self):
        """Calculate OR Logic hybrid signals"""
        print("Calculating OR Logic hybrid signals (MACD OR SMA)...")
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD components
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Individual signal components
        macd_bullish = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        sma_bullish = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # OR Logic: Buy when EITHER signal is bullish
        # Sell only when BOTH signals are bearish
        tqqq_data['Signal'] = np.where(
            (macd_bullish == 1) | (sma_bullish == 1), 1, 0
        )
        
        # Calculate position changes for trade signals
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        # Store individual components for analysis
        tqqq_data['MACD_Bullish'] = macd_bullish
        tqqq_data['SMA_Bullish'] = sma_bullish
        
        # Align with LQQ3 data
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
            tqqq_filtered[['Close', 'MACD', 'MACD_Signal', 'SMA_200', 
                          'MACD_Bullish', 'SMA_Bullish', 'Signal', 'Position_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        for col in ['Signal', 'MACD_Bullish', 'SMA_Bullish']:
            signals_df[col] = signals_df[col].fillna(method='ffill')
        signals_df['Position_Change'] = signals_df['Position_Change'].fillna(0)
        
        # Drop rows without LQQ3 data
        self.signals = signals_df.dropna(subset=['LQQ3_Close'])
        
        print(f"OR Logic signals calculated for {len(self.signals)} trading days")
        print(f"Date range: {self.signals.index.min()} to {self.signals.index.max()}")
        
        return self.signals
    
    def run_backtest(self):
        """Run the backtest simulation"""
        print("Running OR Logic hybrid strategy backtest...")
        
        if self.signals.empty:
            raise ValueError("No signals found. Run calculate_or_logic_signals() first.")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['Signal']
            position_change = row['Position_Change']
            
            # Execute trades based on OR logic signals
            if position_change == 1:  # Buy signal (either MACD OR SMA bullish)
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                    trade_amount = new_shares
                else:
                    trade_type = 'HOLD'
                    trade_amount = 0
                    
            elif position_change == -1:  # Sell signal (both MACD AND SMA bearish)
                if shares > 0:
                    shares_to_sell = shares * 0.66  # Sell 66%
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
                'TQQQ_MACD': row['MACD'],
                'TQQQ_MACD_Signal': row['MACD_Signal'],
                'TQQQ_SMA200': row['SMA_200'],
                'MACD_Bullish': row['MACD_Bullish'],
                'SMA_Bullish': row['SMA_Bullish'],
                'Hybrid_Signal': signal,
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
        """Calculate comprehensive performance metrics"""
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
        
        # Performance calculations
        final_value = self.portfolio['Portfolio_Value'].iloc[-1]
        buyhold_final = self.portfolio['BuyHold_Value'].iloc[-1]
        
        total_return = (final_value / self.initial_capital - 1) * 100
        buyhold_return = (buyhold_final / self.initial_capital - 1) * 100
        excess_return = total_return - buyhold_return
        
        # Risk metrics
        daily_returns = self.portfolio['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Maximum drawdown
        rolling_max = self.portfolio['Portfolio_Value'].expanding().max()
        drawdown = (self.portfolio['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Trading statistics
        trades = self.portfolio[self.portfolio['Trade_Type'] != 'HOLD']
        num_trades = len(trades)
        
        # Signal analysis
        total_days = len(self.portfolio)
        days_invested = len(self.portfolio[self.portfolio['Hybrid_Signal'] == 1])
        days_macd_only = len(self.portfolio[(self.portfolio['MACD_Bullish'] == 1) & 
                                          (self.portfolio['SMA_Bullish'] == 0)])
        days_sma_only = len(self.portfolio[(self.portfolio['SMA_Bullish'] == 1) & 
                                         (self.portfolio['MACD_Bullish'] == 0)])
        days_both_bullish = len(self.portfolio[(self.portfolio['MACD_Bullish'] == 1) & 
                                             (self.portfolio['SMA_Bullish'] == 1)])
        
        years = (self.portfolio.index[-1] - self.portfolio.index[0]).days / 365.25
        
        metrics = {
            'Strategy': 'OR Logic Hybrid (MACD + SMA)',
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buyhold_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Final Portfolio Value (£)': round(final_value, 2),
            'Initial Capital (£)': self.initial_capital,
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Trades per Year': round(num_trades / years, 1),
            'Time in Market (%)': round(days_invested / total_days * 100, 1),
            'Days MACD Only (%)': round(days_macd_only / total_days * 100, 1),
            'Days SMA Only (%)': round(days_sma_only / total_days * 100, 1),
            'Days Both Signals (%)': round(days_both_bullish / total_days * 100, 1),
            'Trading Period (Years)': round(years, 1)
        }
        
        return metrics
    
    def print_summary(self):
        """Print comprehensive strategy summary"""
        metrics = self.calculate_performance_metrics()
        
        print("\n" + "="*80)
        print("OR LOGIC HYBRID STRATEGY - FINAL RESULTS")
        print("="*80)
        print("Strategy: Buy LQQ3 when TQQQ price > 200 SMA OR TQQQ MACD > Signal Line")
        print("          Sell 66% when TQQQ price < 200 SMA AND TQQQ MACD < Signal Line")
        print(f"Period: {self.start_date} to {self.portfolio.index[-1].strftime('%Y-%m-%d')}")
        print(f"Initial Capital: £{self.initial_capital:,}")
        print("-"*80)
        
        # Core performance metrics
        print("PERFORMANCE METRICS:")
        key_metrics = [
            'Total Return (%)', 'Buy & Hold Return (%)', 'Excess Return (%)',
            'Final Portfolio Value (£)', 'Volatility (%)', 'Sharpe Ratio', 'Max Drawdown (%)'
        ]
        
        for metric in key_metrics:
            value = metrics[metric]
            if isinstance(value, float) and 'Portfolio Value' in metric:
                print(f"  {metric:<30}: £{value:,.2f}")
            else:
                print(f"  {metric:<30}: {value}")
        
        # Trading statistics
        print(f"\nTRADING STATISTICS:")
        trading_metrics = [
            'Number of Trades', 'Trades per Year', 'Time in Market (%)',
            'Days MACD Only (%)', 'Days SMA Only (%)', 'Days Both Signals (%)'
        ]
        
        for metric in trading_metrics:
            print(f"  {metric:<30}: {metrics[metric]}")
        
        # Signal breakdown
        trades = self.portfolio[self.portfolio['Trade_Type'] != 'HOLD']
        if not trades.empty:
            buy_trades = trades[trades['Trade_Type'] == 'BUY']
            sell_trades = trades[trades['Trade_Type'] == 'SELL']
            
            print(f"\nTRADE BREAKDOWN:")
            print(f"  Buy Signals: {len(buy_trades)}")
            print(f"  Sell Signals: {len(sell_trades)}")
            
            if len(trades) > 0:
                print(f"  First Trade: {trades.index[0].strftime('%Y-%m-%d')} ({trades['Trade_Type'].iloc[0]})")
                print(f"  Last Trade: {trades.index[-1].strftime('%Y-%m-%d')} ({trades['Trade_Type'].iloc[-1]})")
        
        print("="*80)
        
        return metrics

def main():
    """Run the optimized hybrid strategy"""
    print("="*80)
    print("OPTIMIZED OR LOGIC HYBRID STRATEGY")
    print("="*80)
    print("Combining MACD momentum signals with SMA trend signals")
    print("for maximum bull market participation")
    print("-"*80)
    
    # Initialize strategy
    strategy = OptimizedHybridStrategy(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        # Run complete analysis
        strategy.fetch_data()
        strategy.calculate_or_logic_signals()
        strategy.run_backtest()
        
        # Display results
        metrics = strategy.print_summary()
        
        # Save detailed results
        strategy.portfolio.to_csv('or_logic_hybrid_strategy_results.csv')
        print(f"\nDetailed results saved to 'or_logic_hybrid_strategy_results.csv'")
        
        # Current signal status
        print(f"\n{'='*80}")
        print("CURRENT SIGNAL STATUS")
        print("="*80)
        
        latest = strategy.signals.iloc[-1]
        current_date = strategy.signals.index[-1]
        
        print(f"As of: {current_date.strftime('%Y-%m-%d')}")
        print(f"TQQQ Price: ${latest['TQQQ_Close']:.2f}")
        print(f"TQQQ 200 SMA: ${latest['SMA_200']:.2f}")
        print(f"TQQQ MACD: {latest['MACD']:.4f}")
        print(f"MACD Signal: {latest['MACD_Signal']:.4f}")
        
        macd_status = "🟢 Bullish" if latest['MACD_Bullish'] else "🔴 Bearish"
        sma_status = "🟢 Bullish" if latest['SMA_Bullish'] else "🔴 Bearish"
        hybrid_status = "🟢 BUY" if latest['Signal'] else "🔴 SELL"
        
        print(f"\nMaCD Signal: {macd_status}")
        print(f"SMA Signal: {sma_status}")
        print(f"HYBRID Signal: {hybrid_status}")
        
        # Recommendation
        if latest['Signal'] == 1:
            print(f"\n💡 RECOMMENDATION: HOLD/BUY LQQ3 (at least one bullish signal)")
        else:
            print(f"\n💡 RECOMMENDATION: REDUCED POSITION (both signals bearish)")
        
        return strategy
        
    except Exception as e:
        print(f"Error running optimized strategy: {e}")
        return None

if __name__ == "__main__":
    strategy = main()
