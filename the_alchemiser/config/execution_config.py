#!/usr/bin/env python3
"""
Execution Configuration

Configuration settings for the professional execution system.
Loads settings from the main config.yaml file.
"""

import logging
import os
import yaml
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ExecutionConfig:
    """Configuration for professional execution system."""
    
    # Risk management settings
    max_slippage_bps: float = 20.0
    aggressive_timeout_seconds: float = 2.5
    max_repegs: int = 2
    
    # Market timing settings
    enable_premarket_assessment: bool = True
    market_open_fast_execution: bool = True
    
    # Spread thresholds (in cents)
    tight_spread_threshold: float = 3.0
    wide_spread_threshold: float = 5.0
    
    # Symbol classification
    leveraged_etf_symbols: Optional[List[str]] = None
    high_volume_etfs: Optional[List[str]] = None
    
    @classmethod
    def from_config_file(cls):
        """Load configuration from config.yaml file."""
        # Find config file in common locations
        config_paths = [
            "config.yaml",
            "the_alchemiser/config.yaml",
            "../config.yaml",
            "../../config.yaml"
        ]
        
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path or not os.path.exists(config_path):
            logging.warning("Config file not found, using default execution settings")
            return cls()
            
        try:
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            execution_config = yaml_config.get('execution', {})
            
            return cls(
                max_slippage_bps=float(execution_config.get('max_slippage_bps', 20.0)),
                aggressive_timeout_seconds=float(execution_config.get('aggressive_timeout_seconds', 2.5)),
                max_repegs=int(execution_config.get('max_repegs', 2)),
                enable_premarket_assessment=execution_config.get('enable_premarket_assessment', True),
                market_open_fast_execution=execution_config.get('market_open_fast_execution', True),
                tight_spread_threshold=float(execution_config.get('tight_spread_threshold', 3.0)),
                wide_spread_threshold=float(execution_config.get('wide_spread_threshold', 5.0)),
                leveraged_etf_symbols=execution_config.get('leveraged_etf_symbols'),
                high_volume_etfs=execution_config.get('high_volume_etfs')
            )
            
        except Exception as e:
            logging.error(f"Error loading execution config: {e}")
            return cls()
    
    def get_slippage_tolerance(self, symbol: str) -> float:
        """
        Get slippage tolerance for a symbol.
        
        Args:
            symbol: The symbol to check
            
        Returns:
            float: Slippage tolerance in basis points
        """
        # Use standard slippage for all symbols
        return self.max_slippage_bps
    
    def is_leveraged_etf(self, symbol: str) -> bool:
        """Check if symbol is a leveraged ETF."""
        return bool(self.leveraged_etf_symbols and symbol in self.leveraged_etf_symbols)
    
    def is_high_volume_etf(self, symbol: str) -> bool:
        """Check if symbol is a high-volume ETF."""
        return bool(self.high_volume_etfs and symbol in self.high_volume_etfs)


# Global config instance
_config_instance = None

def get_execution_config() -> ExecutionConfig:
    """Get the global execution configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ExecutionConfig.from_config_file()
    return _config_instance

def reload_execution_config():
    """Reload the execution configuration from file."""
    global _config_instance
    _config_instance = ExecutionConfig.from_config_file()
