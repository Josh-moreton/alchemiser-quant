from trading_strategy_backtest import TradingStrategyBacktest

# Create and run a quick backtest for visualization
backtester = TradingStrategyBacktest(start_date="2012-12-13", initial_capital=10000)

try:
    # Run the backtest
    backtester.fetch_data()
    backtester.calculate_signals()
    backtester.run_backtest()
    
    # Generate the interactive plot
    print("Generating interactive plots...")
    fig = backtester.plot_results()
    
    # Save the plot as HTML
    fig.write_html("backtest_visualization.html")
    print("Interactive plot saved as 'backtest_visualization.html'")
    
    # Also show performance metrics again
    print("\n" + "="*60)
    print("QUICK PERFORMANCE SUMMARY")
    print("="*60)
    metrics = backtester.calculate_performance_metrics()
    for key, value in metrics.items():
        print(f"{key:<25}: {value}")
    
except Exception as e:
    print(f"Error: {e}")
