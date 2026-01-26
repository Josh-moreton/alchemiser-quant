"""Business Unit: shared | Status: current.

Options hedging constants and configuration.
"""

from __future__ import annotations

from .hedge_config import (
    # Thresholds
    CRITICAL_DTE_THRESHOLD,
    DEFAULT_ETF_PRICE_FALLBACK,
    DEFAULT_ETF_PRICES,
    HEDGE_ETFS,
    LIMIT_PRICE_DISCOUNT_FACTOR,
    LIQUIDITY_FILTERS,
    MAX_EXISTING_HEDGE_COUNT,
    MIN_EXPOSURE_RATIO,
    MIN_NAV_THRESHOLD,
    ORDER_POLL_INTERVAL_SECONDS,
    QQQ_PREFERENCE_THRESHOLD,
    SMOOTHING_HEDGE_TEMPLATE,
    STRIKE_MAX_OTM_RATIO,
    STRIKE_MIN_OTM_RATIO,
    TAIL_HEDGE_TEMPLATE,
    VIX_HIGH_THRESHOLD,
    VIX_LOW_THRESHOLD,
    VIX_PROXY_SCALE_FACTOR,
    VIX_PROXY_SYMBOL,
    # Dataclasses
    HedgeETF,
    LiquidityFilters,
    SmoothingHedgeTemplate,
    TailHedgeTemplate,
    # Functions
    get_budget_rate_for_vix,
    get_exposure_multiplier,
)
from .sector_mapping import (
    TICKER_SECTOR_MAP,
    get_hedge_etf,
)

__all__ = [
    "CRITICAL_DTE_THRESHOLD",
    "DEFAULT_ETF_PRICES",
    "DEFAULT_ETF_PRICE_FALLBACK",
    "HEDGE_ETFS",
    "LIMIT_PRICE_DISCOUNT_FACTOR",
    "LIQUIDITY_FILTERS",
    "MAX_EXISTING_HEDGE_COUNT",
    "MIN_EXPOSURE_RATIO",
    "MIN_NAV_THRESHOLD",
    "ORDER_POLL_INTERVAL_SECONDS",
    "QQQ_PREFERENCE_THRESHOLD",
    "SMOOTHING_HEDGE_TEMPLATE",
    "STRIKE_MAX_OTM_RATIO",
    "STRIKE_MIN_OTM_RATIO",
    "TAIL_HEDGE_TEMPLATE",
    "TICKER_SECTOR_MAP",
    "VIX_HIGH_THRESHOLD",
    "VIX_LOW_THRESHOLD",
    "VIX_PROXY_SCALE_FACTOR",
    "VIX_PROXY_SYMBOL",
    "HedgeETF",
    "LiquidityFilters",
    "SmoothingHedgeTemplate",
    "TailHedgeTemplate",
    "get_budget_rate_for_vix",
    "get_exposure_multiplier",
    "get_hedge_etf",
]
