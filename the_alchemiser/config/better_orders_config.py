#!/usr/bin/env python3
"""
Better Orders Configuration

Configuration settings for the enhanced execution system.
Loads settings from the main config.yaml file.
"""

import logging
import os
import yaml
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ExecutionMode(Enum):
    """Execution mode preference."""
    BETTER_ORDERS = "better_orders"  # Use enhanced execution ladder
    STANDARD = "standard"            # Use existing execution
    AUTO = "auto"                    # Automatic based on symbol type

@dataclass
class BetterOrdersConfig:
    """Configuration for better orders execution system."""
    
    # Core settings
    enabled: bool = True
    execution_mode: ExecutionMode = ExecutionMode.AUTO
    
    # Symbol classification
    leveraged_etf_symbols: Optional[List[str]] = None
    high_volume_etfs: Optional[List[str]] = None
    
    # Risk management
    max_slippage_bps: float = 20.0
    aggressive_timeout_seconds: float = 2.5
    max_repegs: int = 2
    
    # Market timing
    enable_premarket_assessment: bool = True
    market_open_fast_execution: bool = True
    
    # Spread thresholds (in cents)
    tight_spread_threshold: float = 3.0
    wide_spread_threshold: float = 5.0
    
    @classmethod
    def from_yaml_config(cls, config_path: Optional[str] = None) -> 'BetterOrdersConfig':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config.yaml file. If None, searches for it.
            
        Returns:
            BetterOrdersConfig: Configuration loaded from YAML
        """
        if config_path is None:
            # Search for config.yaml in common locations
            search_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'config.yaml'),
                os.path.join(os.getcwd(), 'config.yaml'),
                os.path.join(os.getcwd(), 'the_alchemiser', 'config.yaml'),
            ]
            
            config_path = None
            for path in search_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        if not config_path or not os.path.exists(config_path):
            logging.warning("Config file not found, using default better orders settings")
            return cls()
            
        try:
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            better_orders_config = yaml_config.get('better_orders', {})
            
            # Parse execution mode
            execution_mode_str = better_orders_config.get('execution_mode', 'auto')
            try:
                execution_mode = ExecutionMode(execution_mode_str)
            except ValueError:
                logging.warning(f"Invalid execution_mode '{execution_mode_str}', using AUTO")
                execution_mode = ExecutionMode.AUTO
            
            return cls(
                enabled=better_orders_config.get('enabled', True),
                execution_mode=execution_mode,
                leveraged_etf_symbols=better_orders_config.get('leveraged_etf_symbols'),
                high_volume_etfs=better_orders_config.get('high_volume_etfs'),
                max_slippage_bps=float(better_orders_config.get('max_slippage_bps', 20.0)),
                aggressive_timeout_seconds=float(better_orders_config.get('aggressive_timeout_seconds', 2.5)),
                max_repegs=int(better_orders_config.get('max_repegs', 2)),
                enable_premarket_assessment=better_orders_config.get('enable_premarket_assessment', True),
                market_open_fast_execution=better_orders_config.get('market_open_fast_execution', True),
                tight_spread_threshold=float(better_orders_config.get('tight_spread_threshold', 3.0)),
                wide_spread_threshold=float(better_orders_config.get('wide_spread_threshold', 5.0)),
            )
            
        except Exception as e:
            logging.error(f"Error loading better orders config from {config_path}: {e}")
            return cls()  # Return default config on error
    
    def __post_init__(self):
        """Initialize default symbol lists if not provided and not loaded from YAML."""
        if self.leveraged_etf_symbols is None:
            self.leveraged_etf_symbols = [
                "TQQQ", "SQQQ", "TECL", "SPXL", "UPRO", "UVXY", 
                "LABU", "LABD", "SOXL", "FNGU", "FTLS", "FAS"
            ]
        
        if self.high_volume_etfs is None:
            self.high_volume_etfs = [
                "SPY", "QQQ", "TLT", "XLF", "XLK", "XLP", "XLY", 
                "VOX", "VTV", "VOOG", "VOOV", "AGG", "BIL", "BSV"
            ]
    
    def should_use_better_orders(self, symbol: str) -> bool:
        """
        Determine if better orders should be used for a symbol.
        
        Args:
            symbol: The symbol to check
            
        Returns:
            bool: True if better orders should be used
        """
        if not self.enabled:
            return False
            
        if self.execution_mode == ExecutionMode.STANDARD:
            return False
        elif self.execution_mode == ExecutionMode.BETTER_ORDERS:
            return True
        else:  # AUTO mode
            # Use better orders for leveraged ETFs and high-volume ETFs
            return bool((self.leveraged_etf_symbols and symbol in self.leveraged_etf_symbols) or 
                       (self.high_volume_etfs and symbol in self.high_volume_etfs))
    
    def get_slippage_tolerance(self, symbol: str) -> float:
        """
        Get slippage tolerance based on symbol type.
        
        Args:
            symbol: The symbol to check
            
        Returns:
            float: Maximum slippage in basis points
        """
        if self.leveraged_etf_symbols and symbol in self.leveraged_etf_symbols:
            # Higher tolerance for leveraged ETFs due to opportunity cost
            return self.max_slippage_bps
        elif self.high_volume_etfs and symbol in self.high_volume_etfs:
            # Lower tolerance for high-volume ETFs (should have tight spreads)
            return self.max_slippage_bps * 0.5
        else:
            # Standard tolerance for other symbols
            return self.max_slippage_bps * 0.75

# Global configuration instance
better_orders_config = None

def get_better_orders_config() -> BetterOrdersConfig:
    """Get the global better orders configuration, loading from YAML if needed."""
    global better_orders_config
    if better_orders_config is None:
        better_orders_config = BetterOrdersConfig.from_yaml_config()
    return better_orders_config

def reload_better_orders_config(config_path: Optional[str] = None) -> None:
    """
    Reload the global better orders configuration from YAML.
    
    Args:
        config_path: Path to config.yaml file. If None, searches for it.
    """
    global better_orders_config
    better_orders_config = BetterOrdersConfig.from_yaml_config(config_path)

def update_better_orders_config(**kwargs) -> None:
    """
    Update the global better orders configuration.
    
    Args:
        **kwargs: Configuration parameters to update
    """
    global better_orders_config
    if better_orders_config is None:
        better_orders_config = get_better_orders_config()
        
    for key, value in kwargs.items():
        if hasattr(better_orders_config, key):
            setattr(better_orders_config, key, value)
        else:
            raise ValueError(f"Unknown configuration parameter: {key}")

def get_config_summary() -> dict:
    """
    Get a summary of the current better orders configuration.
    
    Returns:
        dict: Configuration summary
    """
    config = get_better_orders_config()
    return {
        'enabled': config.enabled,
        'execution_mode': config.execution_mode.value,
        'max_slippage_bps': config.max_slippage_bps,
        'aggressive_timeout_seconds': config.aggressive_timeout_seconds,
        'max_repegs': config.max_repegs,
        'leveraged_etf_count': len(config.leveraged_etf_symbols or []),
        'high_volume_etf_count': len(config.high_volume_etfs or []),
        'tight_spread_threshold': config.tight_spread_threshold,
        'wide_spread_threshold': config.wide_spread_threshold,
    }
