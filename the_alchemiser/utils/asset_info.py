#!/usr/bin/env python3
"""
Asset Information Utilities

Handles asset-specific information like fractionability, ETF types, and trading characteristics.
This helps optimize order placement strategies for different asset types.
"""

import logging
from typing import Set, Optional, Dict
from enum import Enum
import os

try:
    from alpaca.trading.client import TradingClient
    from the_alchemiser.core.config import Config
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class AssetType(Enum):
    """Asset type classification for trading optimization."""
    STOCK = "stock"
    ETF = "etf"
    ETN = "etn"
    LEVERAGED_ETF = "leveraged_etf"
    CRYPTO = "crypto"
    UNKNOWN = "unknown"


class FractionabilityDetector:
    """
    Detects and handles non-fractionable assets using real-time Alpaca API data.
    
    Professional trading systems need to handle assets that don't support
    fractional shares. This system queries Alpaca's API for authoritative
    fractionability information with intelligent caching and fallbacks.
    """
    
    def __init__(self, trading_client: Optional[TradingClient] = None):
        """
        Initialize with optional trading client for API access.
        
        Args:
            trading_client: Alpaca trading client (will create one if None)
        """
        self.trading_client = trading_client
        self._fractionability_cache: Dict[str, bool] = {}
        
        # Backup prediction patterns (used only when API is unavailable)
        # NOTE: These were mostly wrong based on API testing, so we only use them as fallback
        self.backup_known_non_fractionable = {
            'FNGU',  # Confirmed non-fractionable via API
            # Most others were wrong, so we'll rely on API
        }
        
        # Initialize trading client if needed
        if self.trading_client is None and ALPACA_AVAILABLE:
            try:
                from the_alchemiser.core.secrets.secrets_manager import SecretsManager
                secrets_manager = SecretsManager()
                paper_api_key, paper_secret_key = secrets_manager.get_alpaca_keys(paper_trading=True)
                
                if paper_api_key and paper_secret_key:
                    self.trading_client = TradingClient(
                        api_key=paper_api_key,
                        secret_key=paper_secret_key,
                        paper=True
                    )
                    logging.info("✅ FractionabilityDetector initialized with Alpaca API access")
                else:
                    logging.warning("⚠️ No Alpaca API keys found, using fallback prediction")
            except Exception as e:
                logging.warning(f"⚠️ Could not initialize Alpaca client: {e}, using fallback prediction")
    
    def _query_alpaca_fractionability(self, symbol: str) -> Optional[bool]:
        """
        Query Alpaca API for definitive fractionability information.
        
        Args:
            symbol: Stock symbol to query
            
        Returns:
            True if fractionable, False if not, None if API unavailable/error
        """
        if not self.trading_client:
            return None
        
        try:
            asset = self.trading_client.get_asset(symbol)
            fractionable = getattr(asset, 'fractionable', None)
            
            if fractionable is not None:
                logging.debug(f"📡 Alpaca API: {symbol} fractionable = {fractionable}")
                return bool(fractionable)
            else:
                logging.warning(f"⚠️ Alpaca API returned no fractionability info for {symbol}")
                return None
                
        except Exception as e:
            logging.warning(f"⚠️ Alpaca API error for {symbol}: {e}")
            return None
    
    def is_fractionable(self, symbol: str, use_cache: bool = True) -> bool:
        """
        Determine if an asset supports fractional shares using Alpaca API.
        
        This is the authoritative method that should be used instead of 
        is_likely_non_fractionable() when possible.
        
        Args:
            symbol: Stock symbol to check
            use_cache: Whether to use cached results
            
        Returns:
            True if asset supports fractional shares, False otherwise
        """
        symbol = symbol.upper()
        
        # Check cache first
        if use_cache and symbol in self._fractionability_cache:
            cached_result = self._fractionability_cache[symbol]
            logging.debug(f"📋 Cache hit: {symbol} fractionable = {cached_result}")
            return cached_result
        
        # Query Alpaca API for authoritative answer
        api_result = self._query_alpaca_fractionability(symbol)
        
        if api_result is not None:
            # Cache the API result
            self._fractionability_cache[symbol] = api_result
            return api_result
        
        # Fallback to backup prediction if API unavailable
        logging.info(f"🔄 Using fallback prediction for {symbol} (API unavailable)")
        fallback_result = self._fallback_fractionability_prediction(symbol)
        
        # Cache the fallback result with a warning
        self._fractionability_cache[symbol] = fallback_result
        return fallback_result
    
    def _fallback_fractionability_prediction(self, symbol: str) -> bool:
        """
        Fallback prediction when API is unavailable (mostly deprecated).
        
        Args:
            symbol: Stock symbol to predict
            
        Returns:
            True if likely fractionable, False if likely not
        """
        symbol = symbol.upper()
        
        # Known non-fractionable from API testing
        if symbol in self.backup_known_non_fractionable:
            return False
        
        # Conservative approach: assume fractionable unless proven otherwise
        # This is safer since most assets are fractionable according to API testing
        return True
    
    def is_likely_non_fractionable(self, symbol: str) -> bool:
        """
        Legacy method for backward compatibility.
        
        DEPRECATED: Use is_fractionable() instead for API-based results.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            True if likely non-fractionable, False otherwise
        """
        logging.warning("⚠️ is_likely_non_fractionable() is deprecated, use is_fractionable() instead")
        return not self.is_fractionable(symbol)
    
    def get_asset_type(self, symbol: str) -> AssetType:
        """
        Classify asset type for optimization strategies.
        
        Args:
            symbol: Stock symbol to classify
            
        Returns:
            AssetType enum value
        """
        symbol = symbol.upper()
        
        # Check if it's non-fractionable first
        if not self.is_fractionable(symbol):
            return AssetType.LEVERAGED_ETF  # Most non-fractionable assets are leveraged products
        
        # Regular ETFs (common patterns)
        if (symbol in ['SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'BIL'] or
            symbol.startswith('VT') or symbol.startswith('VO')):
            return AssetType.ETF
        
        # Assume stocks by default
        return AssetType.STOCK
    
    def should_use_notional_order(self, symbol: str, quantity: float) -> bool:
        """
        Determine if we should use notional (dollar) orders instead of quantity orders.
        
        Professional strategy using real API data:
        - Use notional orders for non-fractionable assets
        - Use notional orders for small fractional quantities
        - Use quantity orders for large whole-share quantities
        
        Args:
            symbol: Stock symbol
            quantity: Intended quantity to trade
            
        Returns:
            True if should use notional order, False for quantity order
        """
        # Always use notional for non-fractionable assets (API-confirmed)
        if not self.is_fractionable(symbol):
            return True
        
        # Use notional for very small fractional amounts (< 1 share)
        if quantity < 1.0:
            return True
        
        # Use notional if the fractional part is significant (> 0.1)
        if quantity % 1.0 > 0.1:
            return True
        
        # Use quantity orders for clean whole shares of fractionable assets
        return False
    
    def convert_to_whole_shares(self, symbol: str, quantity: float, current_price: float) -> tuple[float, bool]:
        """
        Convert fractional quantity to whole shares for non-fractionable assets.
        
        Uses real API data to determine if conversion is needed.
        
        Args:
            symbol: Stock symbol
            quantity: Fractional quantity desired
            current_price: Current price per share
            
        Returns:
            Tuple of (adjusted_quantity, used_rounding)
        """
        # Only convert if asset is actually non-fractionable (API-confirmed)
        if self.is_fractionable(symbol):
            return quantity, False
        
        # Round down to whole shares for non-fractionable assets
        whole_shares = int(quantity)
        used_rounding = whole_shares != quantity
        
        if used_rounding:
            original_value = quantity * current_price
            new_value = whole_shares * current_price
            logging.info(f"🔄 API-confirmed non-fractionable {symbol}: {quantity:.6f} → {whole_shares} shares "
                        f"(${original_value:.2f} → ${new_value:.2f})")
        
        return float(whole_shares), used_rounding
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the fractionability cache."""
        return {
            'cached_symbols': len(self._fractionability_cache),
            'fractionable_count': sum(1 for v in self._fractionability_cache.values() if v),
            'non_fractionable_count': sum(1 for v in self._fractionability_cache.values() if not v)
        }


# Global instance for easy access (will initialize with API access if available)
fractionability_detector = FractionabilityDetector()
