#!/usr/bin/env python3
"""
Check cached LSE data and run portfolio analysis
"""

import os
import pickle
import pandas as pd
from datetime import datetime

DATA_FOLDER = "lse_ticker_data"

def check_cache_status():
    """Check what's currently cached and ready to use."""
    print("=" * 80)
    print("LSE CACHE STATUS CHECK")
    print("=" * 80)
    
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Data folder {DATA_FOLDER} not found!")
        return False
    
    # Load ticker info
    ticker_info_file = os.path.join(DATA_FOLDER, 'ticker_info.pkl')
    if os.path.exists(ticker_info_file):
        with open(ticker_info_file, 'rb') as f:
            ticker_info = pickle.load(f)
        print(f"✅ Ticker info loaded: {len(ticker_info)} entries")
    else:
        ticker_info = {}
        print("⚠️  No ticker info found")
    
    # Count cached files
    cache_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.pkl') and f != 'ticker_info.pkl']
    print(f"📁 Cached data files: {len(cache_files)}")
    
    if len(cache_files) == 0:
        print("❌ No cached ticker data found!")
        return False
    
    # Sample a few files to check data quality
    sample_files = cache_files[:5]
    successful_loads = 0
    
    print(f"\n🔍 Sampling {len(sample_files)} cache files:")
    for cache_file in sample_files:
        ticker = cache_file.replace('_', '.').replace('.pkl', '')
        try:
            with open(os.path.join(DATA_FOLDER, cache_file), 'rb') as f:
                data = pickle.load(f)
                successful_loads += 1
                asset_type = ticker_info.get(ticker, {}).get('type', 'Unknown')
                print(f"  ✅ {ticker} ({asset_type}): {len(data)} days, {data.index[0].date()} to {data.index[-1].date()}")
        except Exception as e:
            print(f"  ❌ {ticker}: Error loading - {e}")
    
    if successful_loads == 0:
        print("❌ No cache files could be loaded!")
        return False
    
    # Check cache age
    first_file = os.path.join(DATA_FOLDER, cache_files[0])
    cache_date = datetime.fromtimestamp(os.path.getmtime(first_file))
    cache_age = datetime.now() - cache_date
    
    print(f"\n📅 Cache created: {cache_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"⏰ Cache age: {cache_age.days} days, {cache_age.seconds // 3600} hours")
    
    # Asset type breakdown
    if ticker_info:
        print(f"\n📊 Asset type breakdown (from metadata):")
        asset_counts = {}
        for ticker, info in ticker_info.items():
            asset_type = info.get('type', 'Unknown')
            asset_counts[asset_type] = asset_counts.get(asset_type, 0) + 1
        
        for asset_type, count in sorted(asset_counts.items()):
            print(f"  {asset_type}: {count}")
    
    # Check for LQQ3
    lqq3_file = os.path.join(DATA_FOLDER, 'LQQ3_L.pkl')
    if os.path.exists(lqq3_file):
        print(f"\n🎯 LQQ3.L: ✅ Available in cache")
    else:
        print(f"\n🎯 LQQ3.L: ❌ Not found in cache")
    
    print(f"\n💾 Total cache size: {sum(os.path.getsize(os.path.join(DATA_FOLDER, f)) for f in os.listdir(DATA_FOLDER) if f.endswith('.pkl')) / 1024 / 1024:.1f} MB")
    
    print(f"\n🚀 RECOMMENDATION:")
    if len(cache_files) >= 100:
        print(f"Your cache has {len(cache_files)} tickers - MORE than enough for portfolio optimization!")
        print("✅ Ready to run portfolio analysis!")
        print("\nRun: python run_lse_portfolio_analysis.py")
        return True
    else:
        print(f"Your cache has only {len(cache_files)} tickers - might want to download more.")
        print("Consider running the data downloader again.")
        return False

if __name__ == "__main__":
    check_cache_status()
