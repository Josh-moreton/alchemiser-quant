from advanced_strategy_testing import AdvancedTradingStrategyBacktest
import pandas as pd

def analyze_best_strategies():
    """Detailed analysis of the top performing strategies"""
    
    print("="*80)
    print("DETAILED ANALYSIS OF TOP PERFORMING STRATEGIES")
    print("="*80)
    
    # Test the top 3 strategies in detail
    strategies_to_analyze = [
        ('MACD (12/26/9)', 'calculate_signals_macd', {}),
        ('Multi-Indicator Trend Following', 'calculate_signals_trend_following_combo', {}),
        ('Basic 200-day SMA', 'calculate_signals_basic_sma', {}),
    ]
    
    for strategy_name, method_name, params in strategies_to_analyze:
        print(f"\n{'='*60}")
        print(f"ANALYZING: {strategy_name}")
        print(f"{'='*60}")
        
        try:
            # Create backtester
            backtester = AdvancedTradingStrategyBacktest(
                start_date="2012-12-13",
                initial_capital=10000
            )
            
            # Run strategy
            backtester.fetch_data()
            method = getattr(backtester, method_name)
            method(**params)
            backtester.run_backtest()
            metrics = backtester.calculate_performance_metrics()
            
            # Calculate additional metrics
            trades = backtester.portfolio[backtester.portfolio['Trade_Type'] != 'HOLD']
            
            # Time in market
            bullish_days = len(backtester.signals[backtester.signals['Signal'] == 1])
            total_days = len(backtester.signals)
            time_in_market = bullish_days / total_days * 100
            
            # Average holding period
            signal_changes = backtester.signals[backtester.signals['Position_Change'] != 0]
            if len(signal_changes) > 1:
                holding_periods = []
                for i in range(0, len(signal_changes)-1, 2):
                    if i+1 < len(signal_changes):
                        start_date = signal_changes.index[i]
                        end_date = signal_changes.index[i+1]
                        holding_periods.append((end_date - start_date).days)
                avg_holding_period = sum(holding_periods) / len(holding_periods) if holding_periods else 0
            else:
                avg_holding_period = 0
            
            # Print detailed results
            print(f"Performance Metrics:")
            print(f"  Total Return: {metrics['Total Return (%)']}%")
            print(f"  Excess Return: {metrics['Excess Return (%)']}%")
            print(f"  Sharpe Ratio: {metrics['Sharpe Ratio']}")
            print(f"  Max Drawdown: {metrics['Max Drawdown (%)']}%")
            print(f"  Volatility: {metrics['Volatility (%)']}%")
            
            print(f"\nTrading Statistics:")
            print(f"  Number of Trades: {metrics['Number of Trades']}")
            print(f"  Time in Market: {time_in_market:.1f}%")
            print(f"  Average Holding Period: {avg_holding_period:.0f} days")
            
            if not trades.empty:
                buy_trades = trades[trades['Trade_Type'] == 'BUY']
                sell_trades = trades[trades['Trade_Type'] == 'SELL']
                print(f"  Buy Signals: {len(buy_trades)}")
                print(f"  Sell Signals: {len(sell_trades)}")
                
                # Years of trading
                years = (backtester.signals.index[-1] - backtester.signals.index[0]).days / 365.25
                trades_per_year = metrics['Number of Trades'] / years
                print(f"  Trades per Year: {trades_per_year:.1f}")
            
            # Annual returns
            print(f"\nYearly Performance:")
            portfolio = backtester.portfolio.copy()
            portfolio['Year'] = portfolio.index.year
            yearly_perf = portfolio.groupby('Year').agg({
                'Portfolio_Value': ['first', 'last'],
                'BuyHold_Value': ['first', 'last']
            })
            
            yearly_perf.columns = ['Strategy_Start', 'Strategy_End', 'BuyHold_Start', 'BuyHold_End']
            yearly_perf['Strategy_Return%'] = ((yearly_perf['Strategy_End'] / yearly_perf['Strategy_Start'] - 1) * 100).round(1)
            yearly_perf['BuyHold_Return%'] = ((yearly_perf['BuyHold_End'] / yearly_perf['BuyHold_Start'] - 1) * 100).round(1)
            yearly_perf['Excess_Return%'] = (yearly_perf['Strategy_Return%'] - yearly_perf['BuyHold_Return%']).round(1)
            
            # Show years where strategy outperformed
            outperformed_years = yearly_perf[yearly_perf['Excess_Return%'] > 0]
            print(f"  Years Outperformed B&H: {len(outperformed_years)}/{len(yearly_perf)} ({len(outperformed_years)/len(yearly_perf)*100:.1f}%)")
            
            if len(outperformed_years) > 0:
                print(f"  Best Year: {yearly_perf['Excess_Return%'].max():.1f}% excess return")
                print(f"  Worst Year: {yearly_perf['Excess_Return%'].min():.1f}% excess return")
            
            # Save detailed results
            filename = f"{strategy_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}_detailed_results.csv"
            backtester.portfolio.to_csv(filename)
            print(f"\nDetailed results saved to: {filename}")
            
        except Exception as e:
            print(f"Error analyzing {strategy_name}: {e}")

def create_best_strategy_visualization():
    """Create visualization for the best performing strategy (MACD)"""
    print(f"\n{'='*60}")
    print("CREATING VISUALIZATION FOR MACD STRATEGY")
    print(f"{'='*60}")
    
    try:
        # Create MACD strategy backtester
        backtester = AdvancedTradingStrategyBacktest(
            start_date="2012-12-13",
            initial_capital=10000
        )
        
        backtester.fetch_data()
        backtester.calculate_signals_macd()
        backtester.run_backtest()
        backtester.calculate_performance_metrics()
        
        # Create the plot (similar to original but adapted for MACD)
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Portfolio Value vs Buy & Hold (MACD Strategy)', 
                          'TQQQ Price vs 200 SMA', 
                          'LQQ3 Price with Trade Signals',
                          'Portfolio Allocation'),
            vertical_spacing=0.08
        )
        
        # Plot 1: Portfolio performance
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=backtester.portfolio['Portfolio_Value'],
                      name='MACD Strategy', 
                      line=dict(color='blue', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=backtester.portfolio['BuyHold_Value'],
                      name='Buy & Hold LQQ3', 
                      line=dict(color='red', width=2)),
            row=1, col=1
        )
        
        # Plot 2: TQQQ vs SMA
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=backtester.portfolio['TQQQ_Price'],
                      name='TQQQ Price', 
                      line=dict(color='green')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=backtester.portfolio['TQQQ_SMA200'],
                      name='TQQQ 200 SMA', 
                      line=dict(color='orange')),
            row=2, col=1
        )
        
        # Plot 3: LQQ3 with trade signals
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=backtester.portfolio['LQQ3_Price'],
                      name='LQQ3 Price', 
                      line=dict(color='purple')),
            row=3, col=1
        )
        
        # Add buy/sell markers
        trades = backtester.portfolio[backtester.portfolio['Trade_Type'] != 'HOLD']
        buy_trades = trades[trades['Trade_Type'] == 'BUY']
        sell_trades = trades[trades['Trade_Type'] == 'SELL']
        
        if not buy_trades.empty:
            fig.add_trace(
                go.Scatter(x=buy_trades.index, 
                          y=buy_trades['LQQ3_Price'],
                          mode='markers',
                          name='Buy Signals',
                          marker=dict(color='green', size=8, symbol='triangle-up')),
                row=3, col=1
            )
        
        if not sell_trades.empty:
            fig.add_trace(
                go.Scatter(x=sell_trades.index, 
                          y=sell_trades['LQQ3_Price'],
                          mode='markers',
                          name='Sell Signals',
                          marker=dict(color='red', size=8, symbol='triangle-down')),
                row=3, col=1
            )
        
        # Plot 4: Portfolio allocation
        portfolio_equity_value = backtester.portfolio['Shares'] * backtester.portfolio['LQQ3_Price']
        
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=backtester.portfolio['Cash'],
                      name='Cash', 
                      fill='tonexty', 
                      fillcolor='lightblue'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=backtester.portfolio.index, 
                      y=portfolio_equity_value,
                      name='LQQ3 Holdings', 
                      fill='tonexty', 
                      fillcolor='lightgreen'),
            row=4, col=1
        )
        
        # Update layout
        fig.update_layout(
            title='MACD Strategy Backtest Results (Best Performing)',
            height=1200,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=4, col=1)
        fig.update_yaxes(title_text="Value (£)", row=1, col=1)
        fig.update_yaxes(title_text="Price ($)", row=2, col=1)
        fig.update_yaxes(title_text="Price (£)", row=3, col=1)
        fig.update_yaxes(title_text="Value (£)", row=4, col=1)
        
        # Save the plot
        fig.write_html("macd_strategy_visualization.html")
        print("MACD strategy visualization saved as 'macd_strategy_visualization.html'")
        
    except Exception as e:
        print(f"Error creating visualization: {e}")

if __name__ == "__main__":
    analyze_best_strategies()
    create_best_strategy_visualization()
