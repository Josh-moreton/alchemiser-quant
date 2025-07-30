#!/usr/bin/env python3
"""
Price Fetching Utilities

This module provides helper functions for price fetching operations,
breaking down verbose price fetching logic into reusable components.
"""

import logging
import time
import pandas as pd
from alpaca.data.requests import StockLatestQuoteRequest


def subscribe_for_real_time(real_time_pricing, symbol):
    """
    Subscribe to real-time data for a symbol with just-in-time subscription.
    
    Args:
        real_time_pricing: Real-time pricing instance
        symbol: Stock symbol to subscribe to
        
    Returns:
        bool: True if subscription was successful, False otherwise
    """
    if not real_time_pricing or not real_time_pricing.is_connected():
        return False
        
    try:
        # Subscribe for trading with high priority
        real_time_pricing.subscribe_for_trading(symbol)
        logging.debug(f"Subscribed to real-time data for {symbol} (order placement)")
        
        # Give a moment for real-time data to flow
        time.sleep(0.8)  # Slightly longer wait for order placement accuracy
        return True
    except Exception as e:
        logging.warning(f"Failed to subscribe to real-time data for {symbol}: {e}")
        return False


def extract_bid_ask(quote):
    """
    Extract bid and ask prices safely from a quote object.
    
    Args:
        quote: Quote object with bid_price and ask_price attributes
        
    Returns:
        tuple: (bid, ask) as floats, (0.0, 0.0) if extraction fails
    """
    bid = 0.0
    ask = 0.0
    
    try:
        if hasattr(quote, 'bid_price') and quote.bid_price:
            bid = float(quote.bid_price)
        if hasattr(quote, 'ask_price') and quote.ask_price:
            ask = float(quote.ask_price)
    except (ValueError, TypeError) as e:
        logging.warning(f"Error extracting bid/ask from quote: {e}")
        
    return bid, ask


def calculate_price_from_bid_ask(bid, ask):
    """
    Calculate the best price from bid and ask values.
    
    Args:
        bid: Bid price
        ask: Ask price
        
    Returns:
        float: Best available price (midpoint preferred, then bid, then ask)
    """
    if bid > 0 and ask > 0:
        return (bid + ask) / 2  # Return midpoint if both available
    elif bid > 0:
        return bid
    elif ask > 0:
        return ask
    else:
        return None


def get_price_from_quote_api(data_client, symbol):
    """
    Get current price from quote API.
    
    Args:
        data_client: Alpaca data client
        symbol: Stock symbol
        
    Returns:
        float: Current price or None if unavailable
    """
    try:
        request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = data_client.get_stock_latest_quote(request)
        
        if latest_quote and symbol in latest_quote:
            quote = latest_quote[symbol]
            bid, ask = extract_bid_ask(quote)
            return calculate_price_from_bid_ask(bid, ask)
            
    except Exception as e:
        logging.warning(f"Error getting quote for {symbol}: {e}")
        
    return None


def get_price_from_historical_fallback(data_provider, symbol):
    """
    Fallback to recent historical data for price.
    
    Args:
        data_provider: Data provider instance
        symbol: Stock symbol
        
    Returns:
        float: Price from recent historical data or None if unavailable
    """
    try:
        logging.debug(f"No current quote for {symbol}, falling back to historical data")
        df = data_provider.get_data(symbol, period="1d", interval="1m")
        
        if df is not None and not df.empty and 'Close' in df.columns:
            price = df['Close'].iloc[-1]
            
            # Ensure scalar value
            if hasattr(price, 'item'):
                price = price.item()
                
            price = float(price)
            return price if not pd.isna(price) else None
            
    except Exception as e:
        logging.warning(f"Error getting historical price for {symbol}: {e}")
        
    return None


def create_cleanup_function(real_time_pricing, symbol):
    """
    Create a cleanup function to unsubscribe from real-time data.
    
    Args:
        real_time_pricing: Real-time pricing instance
        symbol: Stock symbol
        
    Returns:
        function: Cleanup function that unsubscribes from the symbol
    """
    def cleanup():
        """Cleanup function to unsubscribe after order placement."""
        if real_time_pricing:
            try:
                real_time_pricing.unsubscribe_after_trading(symbol)
                logging.debug(f"Unsubscribed from real-time data for {symbol}")
            except Exception as e:
                logging.warning(f"Error unsubscribing from {symbol}: {e}")
    
    return cleanup
