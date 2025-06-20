import pandas as pd
import numpy as np

def analyze_backtest_results():
    """Analyze the detailed backtest results from CSV"""
    try:
        # Read the results
        results = pd.read_csv('backtest_results.csv', index_col=0, parse_dates=True)
        
        print("="*60)
        print("DETAILED BACKTEST ANALYSIS")
        print("="*60)
        
        # Basic info
        print(f"Analysis Period: {results.index[0].strftime('%Y-%m-%d')} to {results.index[-1].strftime('%Y-%m-%d')}")
        print(f"Total Trading Days: {len(results)}")
        print()
        
        # Trade analysis
        trades = results[results['Trade_Type'] != 'HOLD'].copy()
        print("TRADE ANALYSIS:")
        print(f"Total Trades: {len(trades)}")
        
        if len(trades) > 0:
            buy_trades = trades[trades['Trade_Type'] == 'BUY']
            sell_trades = trades[trades['Trade_Type'] == 'SELL']
            
            print(f"Buy Trades: {len(buy_trades)}")
            print(f"Sell Trades: {len(sell_trades)}")
            print()
            
            # Show all trades
            print("TRADE HISTORY:")
            print("-" * 60)
            for date, trade in trades.iterrows():
                trade_date = date.strftime('%Y-%m-%d')
                trade_type = trade['Trade_Type']
                price = trade['LQQ3_Price']
                amount = trade['Trade_Amount']
                portfolio_value = trade['Portfolio_Value']
                
                print(f"{trade_date}: {trade_type:<4} {amount:>8.2f} shares at £{price:>6.2f} | Portfolio: £{portfolio_value:>8,.0f}")
        
        print()
        print("PORTFOLIO COMPOSITION AT END:")
        print("-" * 60)
        final_cash = results['Cash'].iloc[-1]
        final_shares = results['Shares'].iloc[-1]
        final_price = results['LQQ3_Price'].iloc[-1]
        final_equity_value = final_shares * final_price
        final_total = final_cash + final_equity_value
        
        print(f"Cash: £{final_cash:,.2f} ({final_cash/final_total*100:.1f}%)")
        print(f"LQQ3 Holdings: {final_shares:.2f} shares @ £{final_price:.2f} = £{final_equity_value:,.2f} ({final_equity_value/final_total*100:.1f}%)")
        print(f"Total Portfolio Value: £{final_total:,.2f}")
        
        print()
        print("YEAR-BY-YEAR PERFORMANCE:")
        print("-" * 60)
        results['Year'] = results.index.year
        yearly_performance = results.groupby('Year').agg({
            'Portfolio_Value': ['first', 'last'],
            'BuyHold_Value': ['first', 'last']
        }).round(2)
        
        yearly_performance.columns = ['Strategy_Start', 'Strategy_End', 'BuyHold_Start', 'BuyHold_End']
        yearly_performance['Strategy_Return%'] = ((yearly_performance['Strategy_End'] / yearly_performance['Strategy_Start'] - 1) * 100).round(2)
        yearly_performance['BuyHold_Return%'] = ((yearly_performance['BuyHold_End'] / yearly_performance['BuyHold_Start'] - 1) * 100).round(2)
        yearly_performance['Excess_Return%'] = (yearly_performance['Strategy_Return%'] - yearly_performance['BuyHold_Return%']).round(2)
        
        for year, row in yearly_performance.iterrows():
            print(f"{year}: Strategy {row['Strategy_Return%']:>6.1f}% | Buy&Hold {row['BuyHold_Return%']:>6.1f}% | Excess {row['Excess_Return%']:>6.1f}%")
        
        print()
        print("SIGNAL ANALYSIS:")
        print("-" * 60)
        total_days = len(results)
        bullish_days = len(results[results['Signal'] == 1])
        bearish_days = len(results[results['Signal'] == 0])
        
        print(f"Days with bullish signal (TQQQ > 200 SMA): {bullish_days} ({bullish_days/total_days*100:.1f}%)")
        print(f"Days with bearish signal (TQQQ < 200 SMA): {bearish_days} ({bearish_days/total_days*100:.1f}%)")
        
        # Performance during different market conditions
        bullish_returns = results[results['Signal'] == 1]['Daily_Return'].dropna()
        bearish_returns = results[results['Signal'] == 0]['Daily_Return'].dropna()
        
        if len(bullish_returns) > 0 and len(bearish_returns) > 0:
            print(f"Average daily return during bullish periods: {bullish_returns.mean()*100:.3f}%")
            print(f"Average daily return during bearish periods: {bearish_returns.mean()*100:.3f}%")
        
        print("="*60)
        
    except FileNotFoundError:
        print("Error: backtest_results.csv not found. Please run the backtest first.")
    except Exception as e:
        print(f"Error analyzing results: {e}")

if __name__ == "__main__":
    analyze_backtest_results()
