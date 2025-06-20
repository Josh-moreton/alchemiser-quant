#!/usr/bin/env python3
"""
Hybrid Strategy: Combining MACD and 200-day SMA signals
Tests multiple ways to combine both indicators for improved performance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class HybridStrategyTester:
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
    
    def calculate_both_signals(self):
        """Calculate both MACD and SMA signals"""
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        return tqqq_data
    
    def strategy_1_and_filter(self, tqqq_data):
        """Strategy 1: Both signals must agree (AND logic)"""
        strategy_name = "Hybrid: MACD AND SMA (Conservative)"
        
        # Both signals must be bullish to buy
        tqqq_data['Signal'] = np.where(
            (tqqq_data['MACD_Bullish'] == 1) & (tqqq_data['SMA_Bullish'] == 1), 1, 0
        )
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, strategy_name)
    
    def strategy_2_or_filter(self, tqqq_data):
        """Strategy 2: Either signal can trigger (OR logic)"""
        strategy_name = "Hybrid: MACD OR SMA (Aggressive)"
        
        # Either signal can trigger a buy
        tqqq_data['Signal'] = np.where(
            (tqqq_data['MACD_Bullish'] == 1) | (tqqq_data['SMA_Bullish'] == 1), 1, 0
        )
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, strategy_name)
    
    def strategy_3_macd_with_sma_filter(self, tqqq_data):
        """Strategy 3: MACD signals with SMA trend filter"""
        strategy_name = "Hybrid: MACD with SMA Filter"
        
        # Use MACD signals but only when above SMA (trend filter)
        macd_signal = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        sma_filter = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        tqqq_data['Signal'] = np.where(
            (macd_signal == 1) & (sma_filter == 1), 1, 0
        )
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, strategy_name)
    
    def strategy_4_weighted_score(self, tqqq_data):
        """Strategy 4: Weighted scoring system"""
        strategy_name = "Hybrid: Weighted Score (MACD 60%, SMA 40%)"
        
        # Calculate signal strength
        macd_strength = (tqqq_data['MACD'] - tqqq_data['MACD_Signal']) / tqqq_data['MACD_Signal'].abs()
        sma_strength = (tqqq_data['Close'] - tqqq_data['SMA_200']) / tqqq_data['SMA_200']
        
        # Normalize strengths to 0-1 range
        macd_norm = np.where(macd_strength > 0, 1, 0)
        sma_norm = np.where(sma_strength > 0, 1, 0)
        
        # Weighted score (MACD 60%, SMA 40%)
        weighted_score = macd_norm * 0.6 + sma_norm * 0.4
        
        # Signal when score > 0.5 (at least one strong signal)
        tqqq_data['Signal'] = np.where(weighted_score > 0.5, 1, 0)
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, strategy_name)
    
    def strategy_5_adaptive_position_sizing(self, tqqq_data):
        """Strategy 5: Variable position sizing based on signal agreement"""
        strategy_name = "Hybrid: Adaptive Position Sizing"
        
        # Calculate how many signals agree
        macd_signal = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        sma_signal = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Signal strength: 0 = both bearish, 1 = one bullish, 2 = both bullish
        signal_strength = macd_signal + sma_signal
        
        # Position sizing based on agreement
        # 0 signals = 0% position, 1 signal = 50% position, 2 signals = 100% position
        tqqq_data['Position_Size'] = signal_strength / 2.0
        tqqq_data['Signal'] = np.where(signal_strength > 0, 1, 0)  # Any bullish signal
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, strategy_name), tqqq_data['Position_Size']
    
    def strategy_6_sma_with_macd_timing(self, tqqq_data):
        """Strategy 6: SMA trend with MACD timing"""
        strategy_name = "Hybrid: SMA Trend + MACD Timing"
        
        # Only trade when in SMA uptrend, but use MACD for entry/exit timing
        sma_uptrend = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        macd_signal = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        
        # Combine: Must be in SMA uptrend AND have MACD buy signal
        tqqq_data['Signal'] = np.where(
            (sma_uptrend == 1) & (macd_signal == 1), 1, 0
        )
        tqqq_data['Position_Change'] = tqqq_data['Signal'].diff()
        
        return self._align_signals(tqqq_data, strategy_name)
    
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
        
        print(f"{strategy_name}: {len(signals_df)} trading days")
        return signals_df
    
    def run_backtest(self, signals, strategy_name, position_sizes=None):
        """Run backtest for given signals with optional position sizing"""
        print(f"Running {strategy_name} backtest...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for i, (date, row) in enumerate(signals.iterrows()):
            lqq3_price = row['LQQ3_Close']
            signal = row['Signal']
            position_change = row['Position_Change']
            
            # Get position size if provided
            target_position_pct = 1.0  # Default 100%
            if position_sizes is not None and i < len(position_sizes):
                target_position_pct = position_sizes.iloc[i] if not pd.isna(position_sizes.iloc[i]) else 1.0
            
            # Execute trades
            if position_change == 1:  # Buy signal
                if cash > 0:
                    # Use position sizing
                    cash_to_invest = cash * target_position_pct
                    new_shares = cash_to_invest / lqq3_price
                    shares += new_shares
                    cash -= cash_to_invest
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
    """Test all hybrid strategies"""
    print("="*90)
    print("HYBRID STRATEGY TESTING: COMBINING MACD + 200-DAY SMA")
    print("="*90)
    print("Period: December 2012 - June 2025 (12.5 years)")
    print("Initial Capital: £55,000")
    print("Testing 6 different combination approaches...")
    print("-"*90)
    
    # Initialize tester
    tester = HybridStrategyTester(start_date="2012-12-13", initial_capital=55000)
    
    try:
        # Fetch data and calculate signals
        tester.fetch_data()
        tqqq_data = tester.calculate_both_signals()
        
        # Test all hybrid strategies
        strategies = [
            ('strategy_1_and_filter', 'Strategy 1: AND Logic'),
            ('strategy_2_or_filter', 'Strategy 2: OR Logic'),
            ('strategy_3_macd_with_sma_filter', 'Strategy 3: MACD + SMA Filter'),
            ('strategy_4_weighted_score', 'Strategy 4: Weighted Score'),
            ('strategy_6_sma_with_macd_timing', 'Strategy 6: SMA Trend + MACD Timing'),
        ]
        
        results = []
        
        for method_name, display_name in strategies:
            print(f"\n{'='*60}")
            print(f"TESTING: {display_name}")
            print("="*60)
            
            try:
                # Get strategy method
                method = getattr(tester, method_name)
                signals = method(tqqq_data)
                
                # Run backtest
                portfolio = tester.run_backtest(signals, display_name)
                
                # Calculate metrics
                metrics = tester.calculate_metrics(portfolio, display_name)
                results.append(metrics)
                
                # Print key metrics
                print(f"Total Return: {metrics['Total Return (%)']}%")
                print(f"Excess Return: {metrics['Excess Return (%)']}%")
                print(f"Final Value: £{metrics['Final Portfolio Value (£)']:,.2f}")
                print(f"Max Drawdown: {metrics['Max Drawdown (%)']}%")
                print(f"Sharpe Ratio: {metrics['Sharpe Ratio']}")
                print(f"Trades per Year: {metrics['Trades per Year']}")
                
            except Exception as e:
                print(f"Error testing {display_name}: {e}")
                continue
        
        # Test adaptive position sizing separately (requires special handling)
        print(f"\n{'='*60}")
        print("TESTING: Strategy 5: Adaptive Position Sizing")
        print("="*60)
        
        try:
            signals, position_sizes = tester.strategy_5_adaptive_position_sizing(tqqq_data)
            portfolio = tester.run_backtest(signals, "Strategy 5: Adaptive Position Sizing", position_sizes)
            metrics = tester.calculate_metrics(portfolio, "Strategy 5: Adaptive Position Sizing")
            results.append(metrics)
            
            print(f"Total Return: {metrics['Total Return (%)']}%")
            print(f"Excess Return: {metrics['Excess Return (%)']}%")
            print(f"Final Value: £{metrics['Final Portfolio Value (£)']:,.2f}")
            print(f"Max Drawdown: {metrics['Max Drawdown (%)']}%")
            print(f"Sharpe Ratio: {metrics['Sharpe Ratio']}")
            
        except Exception as e:
            print(f"Error testing Adaptive Position Sizing: {e}")
        
        # Display comparison results
        if results:
            print(f"\n{'='*90}")
            print("HYBRID STRATEGY COMPARISON RESULTS")
            print("="*90)
            
            # Sort by excess return
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Excess Return (%)', ascending=False)
            
            # Display top performers
            print(f"{'Strategy':<40} {'Excess Return':<15} {'Total Return':<15} {'Drawdown':<12} {'Sharpe':<8}")
            print("-"*90)
            
            for _, row in results_df.iterrows():
                print(f"{row['Strategy']:<40} {row['Excess Return (%)']:>10.1f}% {row['Total Return (%)']:>12.1f}% {row['Max Drawdown (%)']:>9.1f}% {row['Sharpe Ratio']:>6.2f}")
            
            # Winner
            best_strategy = results_df.iloc[0]
            print(f"\n🏆 BEST HYBRID STRATEGY: {best_strategy['Strategy']}")
            print(f"   Excess Return: {best_strategy['Excess Return (%)']}%")
            print(f"   Total Return: {best_strategy['Total Return (%)']}%")
            print(f"   Final Value: £{best_strategy['Final Portfolio Value (£)']:,.2f}")
            
            # Save results
            results_df.to_csv('hybrid_strategies_comparison.csv', index=False)
            print(f"\n📁 Detailed results saved to 'hybrid_strategies_comparison.csv'")
            
            return results_df
        
    except Exception as e:
        print(f"Error running hybrid strategy tests: {e}")
        return None

if __name__ == "__main__":
    results = main()
