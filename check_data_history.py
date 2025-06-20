import yfinance as yf
import pandas as pd

def check_data_availability():
    """Check how far back we can get data for both tickers"""
    print("Checking data availability for TQQQ and LQQ3.L...")
    
    # Test different start dates
    test_dates = ["2010-01-01", "2011-01-01", "2012-01-01", "2013-01-01"]
    
    for start_date in test_dates:
        print(f"\nTesting start date: {start_date}")
        try:
            # Fetch TQQQ
            tqqq = yf.download('TQQQ', start=start_date, end="2025-06-20", progress=False)
            if tqqq.columns.nlevels > 1:
                tqqq.columns = tqqq.columns.get_level_values(0)
            
            # Fetch LQQ3.L  
            lqq3 = yf.download('LQQ3.L', start=start_date, end="2025-06-20", progress=False)
            if lqq3.columns.nlevels > 1:
                lqq3.columns = lqq3.columns.get_level_values(0)
            
            print(f"  TQQQ: {len(tqqq)} days ({tqqq.index.min()} to {tqqq.index.max()})")
            print(f"  LQQ3: {len(lqq3)} days ({lqq3.index.min()} to {lqq3.index.max()})")
            
            # Find common date range
            if not tqqq.empty and not lqq3.empty:
                common_start = max(tqqq.index.min(), lqq3.index.min())
                common_end = min(tqqq.index.max(), lqq3.index.max())
                print(f"  Common range: {common_start} to {common_end}")
                
                # Calculate potential trading days
                common_tqqq = tqqq.loc[common_start:common_end]
                common_lqq3 = lqq3.loc[common_start:common_end]
                print(f"  TQQQ in common range: {len(common_tqqq)} days")
                print(f"  LQQ3 in common range: {len(common_lqq3)} days")
        
        except Exception as e:
            print(f"  Error with {start_date}: {e}")
    
    # Try to find the earliest possible start date
    print(f"\nFinding earliest available data...")
    try:
        # Get max available history
        tqqq_max = yf.download('TQQQ', period="max", progress=False)
        lqq3_max = yf.download('LQQ3.L', period="max", progress=False)
        
        if tqqq_max.columns.nlevels > 1:
            tqqq_max.columns = tqqq_max.columns.get_level_values(0)
        if lqq3_max.columns.nlevels > 1:
            lqq3_max.columns = lqq3_max.columns.get_level_values(0)
        
        print(f"TQQQ earliest: {tqqq_max.index.min()} ({len(tqqq_max)} total days)")
        print(f"LQQ3 earliest: {lqq3_max.index.min()} ({len(lqq3_max)} total days)")
        
        # Best common start date
        best_start = max(tqqq_max.index.min(), lqq3_max.index.min())
        print(f"Recommended start date: {best_start}")
        
        # Years of data
        years = (pd.Timestamp.now() - best_start).days / 365.25
        print(f"Total years of data available: {years:.1f} years")
        
    except Exception as e:
        print(f"Error getting max history: {e}")

if __name__ == "__main__":
    check_data_availability()
