"""Business Unit: indicators | Status: current.

Technical Indicators Microservice.

This module provides technical analysis indicators as a dedicated Lambda function.
It encapsulates all pandas-dependent indicator calculations, allowing the Strategy
Lambda to remain lightweight (<50MB) by invoking this service synchronously.

Supported indicators:
- RSI (Relative Strength Index) using Wilder's smoothing
- Simple Moving Averages (SMA)
- Exponential Moving Averages (EMA)
- Cumulative Returns
- Standard Deviation of Returns
- Maximum Drawdown
- Moving Average Returns

The service reads market data from the S3 data lake (Parquet files) and returns
computed indicator values via the TechnicalIndicator DTO.
"""

from __future__ import annotations

from .indicator_service import IndicatorComputationError, IndicatorService
from .indicator_utils import FALLBACK_INDICATOR_VALUE, safe_get_indicator
from .indicators import TechnicalIndicators
from .lambda_handler import lambda_handler

__all__ = [
    "FALLBACK_INDICATOR_VALUE",
    "IndicatorComputationError",
    "IndicatorService",
    "TechnicalIndicators",
    "lambda_handler",
    "safe_get_indicator",
]
