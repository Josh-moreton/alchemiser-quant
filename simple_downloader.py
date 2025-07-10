#!/usr/bin/env python3
"""
Simple LSE Data Downloader - Back to Basics
Just download the damn data without overthinking it.
"""

import yfinance as yf
import pandas as pd
import os
import pickle
from datetime import datetime
import time

# Simple configuration
DATA_FOLDER = "lse_ticker_data"
# START_DATE is no longer needed, we will fetch all available history.

def load_lse_tickers(csv_file="All_LSE.csv"):
    """Load LSE tickers from the CSV file."""
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} total instruments from {csv_file}")
    
    # Filter by asset types we want
    asset_types = ['SHRS', 'ETFS', 'ETCS', 'OTHR', 'ETNS'] # Added ETNS to include LQQ3
    filtered_df = df[df['MiFIR Identifier Code'].isin(asset_types)].copy()
    print(f"Filtered to {len(filtered_df)} instruments")
    
    # Add .L suffix for yfinance
    tickers = [ticker + ".L" for ticker in filtered_df['Ticker'].tolist()]
    
    # Create ticker info mapping
    ticker_info = {}
    for _, row in filtered_df.iterrows():
        ticker_with_suffix = row['Ticker'] + ".L"
        ticker_info[ticker_with_suffix] = {
            'name': row['Instrument Name'],
            'issuer': row['Issuer Name'], 
            'type': row['MiFIR Identifier Description']
        }
    
    return tickers, ticker_info

def download_ticker_simple(ticker):
    """Download ticker data with minimal fuss."""
    try:
        # Use period="max" to get all available daily data.
        data = yf.download(ticker, period="max", progress=False, auto_adjust=True)
        
        if data.empty:
            return None, "No data returned"
        
        # auto_adjust=True means we'll have 'Close' which is adjusted.
        if 'Close' not in data.columns:
            return None, "No 'Close' column in data"
            
        close_data = data[['Close']].copy()
        
        # Basic quality checks
        close_data = close_data.dropna()
        
        if len(close_data) < 500:  # At least ~2 years of data
            return None, f"Not enough data ({len(close_data)} days)"
        
        return close_data, None
        
    except Exception as e:
        # Provide more specific error messages for common yfinance issues
        error_str = str(e)
        if "No timezone found" in error_str:
            return None, "Possibly delisted (no timezone)"
        if "Period 'max' is invalid" in error_str:
            return None, "Invalid period (yfinance error)"
        # Fallback for other errors
        return None, str(e).replace('\n', ' ').strip()[:120]

def main():
    print("=" * 60)
    print("SIMPLE LSE DATA DOWNLOADER")
    print("=" * 60)
    
    # Create data folder
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    # Load tickers
    print("Loading tickers...")
    all_tickers, ticker_info = load_lse_tickers()
    print(f"Found {len(all_tickers)} total tickers in source file.")

    # Check for existing files to avoid re-downloading
    existing_files = os.listdir(DATA_FOLDER)
    existing_tickers = {f.replace('_', '.').replace('.pkl', '') for f in existing_files if f.endswith('.pkl')}
    print(f"Found {len(existing_tickers)} tickers already in cache.")

    # Determine which tickers to download
    tickers_to_download = [t for t in all_tickers if t not in existing_tickers]
    
    if not tickers_to_download:
        print("\nCache is already up to date. Exiting.")
        return

    print(f"Will attempt to download {len(tickers_to_download)} new tickers.")
    
    # Save ticker info (always save the full mapping)
    with open(os.path.join(DATA_FOLDER, 'ticker_info.pkl'), 'wb') as f:
        pickle.dump(ticker_info, f)
    
    # Download one by one with progress
    successful = 0
    failed = 0
    failed_downloads = []
    
    print("\nDownloading new data...")
    start_time = time.time()
    for i, ticker in enumerate(tickers_to_download):
        # Progress report for new downloads
        if i > 0 and i % 100 == 0:
            elapsed = time.time() - start_time
            print(f"Progress: {i}/{len(tickers_to_download)} ({successful} successful, {failed} failed) in {elapsed:.0f}s")

        data, error = download_ticker_simple(ticker)
        
        if data is not None:
            # Save to cache
            ticker_file = ticker.replace('.', '_') + '.pkl'
            filepath = os.path.join(DATA_FOLDER, ticker_file)
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            successful += 1
            
            # Always show success
            asset_type = ticker_info.get(ticker, {}).get('type', 'Unknown')
            print(f"✓ {ticker} ({asset_type}) - {len(data)} days")
        else:
            failed += 1
            failed_downloads.append({'ticker': ticker, 'error': error})
            # Always show failure
            print(f"✗ {ticker}: {error}")
        
        # Small delay to be polite to Yahoo
        time.sleep(0.05) # Slightly reduced delay
    
    print(f"\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"✓ New tickers downloaded: {successful}")
    print(f"✗ New tickers failed: {failed}")
    if tickers_to_download:
        print(f"Success rate for this run: {successful/len(tickers_to_download)*100:.1f}%")
    
    # Save failed downloads to a file
    if failed_downloads:
        failed_df = pd.DataFrame(failed_downloads)
        failed_filename = "failed_downloads.csv"
        failed_df.to_csv(failed_filename, index=False)
        print(f"\nSaved {len(failed_downloads)} failed download attempts to {failed_filename}")

        # Automatically remove failed tickers from the source CSV
        try:
            source_csv_path = "All_LSE.csv"
            source_df = pd.read_csv(source_csv_path)
            original_count = len(source_df)
            
            # Get the tickers to remove, stripping the '.L' suffix
            tickers_to_remove = {item['ticker'].replace('.L', '') for item in failed_downloads}
            
            # Filter the dataframe, keeping only tickers NOT in the removal list
            cleaned_df = source_df[~source_df['Ticker'].isin(tickers_to_remove)]
            
            if len(cleaned_df) < original_count:
                cleaned_df.to_csv(source_csv_path, index=False)
                removed_count = original_count - len(cleaned_df)
                print(f"Removed {removed_count} failed tickers from {source_csv_path}.")
            else:
                print(f"No tickers needed to be removed from {source_csv_path}.")

        except Exception as e:
            print(f"Error updating {source_csv_path}: {e}")

    total_files = len([f for f in os.listdir(DATA_FOLDER) if f.endswith('.pkl')])
    print(f"\nTotal tickers in cache: {total_files}")
    if total_files > 0:
        total_size = sum(os.path.getsize(os.path.join(DATA_FOLDER, f)) 
                        for f in os.listdir(DATA_FOLDER) if f.endswith('.pkl'))
        print(f"Total cache size: {total_size/1024/1024:.1f} MB")
    
    print(f"Ready for portfolio analysis!")

if __name__ == "__main__":
    main()
