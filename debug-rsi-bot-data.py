import pandas as pd
from core.data_provider import UnifiedDataProvider
from core.indicators import TechnicalIndicators
import logging
from core.logging_utils import setup_logging

# Setup logging
setup_logging()

def compare_rsi_calculations():
    """Compare RSI calculations using bot's data provider vs debug script"""
    
    # Use bot's data provider
    data_provider = UnifiedDataProvider(paper_trading=True)
    indicators = TechnicalIndicators()
    
    # Get IOO data using bot's method
    ioo_data = data_provider.get_data("IOO")
    
    if ioo_data.empty:
        print("No IOO data from bot's data provider")
        return
    
    print("IOO data from bot's data provider:")
    print(f"Data shape: {ioo_data.shape}")
    print(f"Date range: {ioo_data.index[0]} to {ioo_data.index[-1]}")
    print("\nLast 5 close prices:")
    print(ioo_data['Close'].tail())
    
    # Calculate RSI using bot's method
    close_prices = ioo_data['Close']
    bot_rsi = indicators.rsi(close_prices, 10)
    
    print(f"\nBot's RSI calculation:")
    print(f"Latest IOO RSI(10): {bot_rsi.iloc[-1]:.2f}")
    print("\nLast 10 RSI values:")
    print(bot_rsi.tail(10))
    
    # Compare with manual calculation from debug script
    print(f"\n" + "="*50)
    print("COMPARISON:")
    print(f"Bot's method:    {bot_rsi.iloc[-1]:.2f}")
    print(f"Debug script:    74.68 (from your earlier debug script)")
    print(f"Difference:      {bot_rsi.iloc[-1] - 74.68:.2f}")
    
    # Show the actual close prices being used
    print(f"\nClose prices used for RSI calculation:")
    print(close_prices.tail(15))  # Show more data for RSI calculation context

if __name__ == "__main__":
    compare_rsi_calculations()
