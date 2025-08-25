#!/usr/bin/env python3
"""
Execution Configuration

Configuration settings for the professional execution system.
Loads settings from the global application configuration.
"""

import logging
from dataclasses import dataclass

from .config import load_settings


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
    leveraged_etf_symbols: list[str] | None = None
    high_volume_etfs: list[str] | None = None

    @classmethod
    def from_settings(cls) -> "ExecutionConfig":
        """Load configuration from application settings."""
        try:
            execution = load_settings().execution
            return cls(
                max_slippage_bps=execution.max_slippage_bps,
                aggressive_timeout_seconds=execution.aggressive_timeout_seconds,
                max_repegs=execution.max_repegs,
                enable_premarket_assessment=execution.enable_premarket_assessment,
                market_open_fast_execution=execution.market_open_fast_execution,
                tight_spread_threshold=execution.tight_spread_threshold,
                wide_spread_threshold=execution.wide_spread_threshold,
                leveraged_etf_symbols=execution.leveraged_etf_symbols,
                high_volume_etfs=execution.high_volume_etfs,
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
_config_instance: ExecutionConfig | None = None


def get_execution_config() -> ExecutionConfig:
    """Get the global execution configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ExecutionConfig.from_settings()
    return _config_instance


def reload_execution_config() -> None:
    """Reload the execution configuration from settings."""
    global _config_instance
    _config_instance = ExecutionConfig.from_settings()
