"""Business Unit: shared | Status: current.

Utility functions for options hedging module.

Provides shared utilities for market data access and price fetching.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from ..logging import get_logger
from .constants import DEFAULT_ETF_PRICE_FALLBACK, DEFAULT_ETF_PRICES

if TYPE_CHECKING:
    from ..config.container import ApplicationContainer

logger = get_logger(__name__)


def get_underlying_price(container: ApplicationContainer, symbol: str) -> Decimal:
    """Get current price of underlying ETF.

    Attempts to fetch real-time price via AlpacaManager.
    Falls back to DEFAULT_ETF_PRICES on API failure or invalid data.

    Args:
        container: Application DI container for accessing AlpacaManager
        symbol: ETF symbol (QQQ, SPY, XLK, etc.)

    Returns:
        Current price from market data or fallback estimate

    Note:
        - Uses mid price (bid + ask) / 2 for fair value
        - Validates that prices are positive before using
        - Timeout protection via AlpacaManager's error handling
        - Logs price source for observability

    Examples:
        >>> container = ApplicationContainer.create_for_environment("production")
        >>> price = get_underlying_price(container, "QQQ")
        >>> print(price)  # Decimal('485.50') from live market data

    """
    try:
        # Attempt to get real-time quote via AlpacaManager
        alpaca_manager = container.infrastructure.alpaca_manager()
        quote = alpaca_manager.get_latest_quote(symbol)

        # Validate quote has valid positive prices
        # Note: QuoteModel fields are non-optional, but we check None explicitly
        # for safety. We also require positive prices to ensure valid mid-price calc.
        if quote is not None and quote.bid_price > 0 and quote.ask_price > 0:
            # Use mid price for fair value
            # Explicit Decimal type ensures proper arithmetic
            mid_price: Decimal = (quote.bid_price + quote.ask_price) / Decimal("2")
            logger.info(
                "Using real-time ETF price",
                symbol=symbol,
                price=str(mid_price),
                bid=str(quote.bid_price),
                ask=str(quote.ask_price),
                price_source="live_market_data",
            )
            return mid_price
    except Exception as e:
        logger.warning(
            "Failed to fetch real-time ETF price, using fallback",
            symbol=symbol,
            error=str(e),
            price_source="fallback",
        )

    # Fallback to hardcoded prices
    fallback_price = DEFAULT_ETF_PRICES.get(symbol, DEFAULT_ETF_PRICE_FALLBACK)
    logger.info(
        "Using fallback ETF price",
        symbol=symbol,
        price=str(fallback_price),
        price_source="fallback",
    )
    return fallback_price


def calculate_contracts_for_payoff_target(
    underlying_price: Decimal,
    option_delta: Decimal,
    scenario_move: Decimal,
    target_payoff: Decimal,
    nav: Decimal,
) -> int:
    """Size contracts so a scenario move produces target NAV payoff.

    Example: If QQQ drops 20%, hedge should gain 8% of NAV.

    This function calculates the number of option contracts needed to achieve
    a target payoff (as percentage of NAV) for a given scenario move in the
    underlying asset.

    For put options:
    - Scenario price: underlying_price * (1 + scenario_move)
    - Strike estimate: Use delta to approximate OTM percentage
      (15-delta put ≈ 15% OTM for standard options)
    - Option payoff per contract: max(0, strike - scenario_price) * 100

    Args:
        underlying_price: Current price of underlying asset (e.g., QQQ at $500)
        option_delta: Target put delta as positive decimal (e.g., 0.15 for 15-delta)
        scenario_move: Scenario move as decimal (e.g., -0.20 for -20% crash)
        target_payoff: Target payoff as % of NAV (e.g., 0.08 for +8% NAV)
        nav: Portfolio net asset value in dollars

    Returns:
        Number of contracts needed (minimum 1)

    Examples:
        >>> # QQQ at $500, 15-delta put, -20% scenario → +8% NAV target
        >>> calculate_contracts_for_payoff_target(
        ...     underlying_price=Decimal("500"),
        ...     option_delta=Decimal("0.15"),
        ...     scenario_move=Decimal("-0.20"),
        ...     target_payoff=Decimal("0.08"),
        ...     nav=Decimal("100000")
        ... )
        3  # Need 3 contracts

    """
    # Target NAV payoff in dollars
    target_payoff_dollars = nav * target_payoff

    # Calculate scenario price after the move
    scenario_price = underlying_price * (Decimal("1") + scenario_move)

    # Estimate strike from delta
    # For puts, delta indicates approximate OTM percentage
    # 15-delta ≈ 15% OTM, so strike ≈ underlying * (1 - delta)
    # This is an approximation; actual relationship varies by volatility
    delta_to_otm_pct = option_delta
    strike = underlying_price * (Decimal("1") - delta_to_otm_pct)

    # Calculate option payoff per contract for scenario move
    # For puts: max(0, strike - scenario_price) * 100 shares
    option_payoff_per_contract = max(Decimal("0"), strike - scenario_price) * 100

    # Avoid division by zero
    if option_payoff_per_contract <= 0:
        logger.warning(
            "Option payoff per contract is zero or negative",
            strike=str(strike),
            scenario_price=str(scenario_price),
            option_delta=str(option_delta),
        )
        return 1

    # Calculate required contracts
    contracts = target_payoff_dollars / option_payoff_per_contract

    # Round up and ensure minimum 1 contract
    contracts_int = max(1, int(contracts + Decimal("0.5")))

    logger.info(
        "Calculated contracts for payoff target",
        underlying_price=str(underlying_price),
        scenario_move=str(scenario_move),
        strike=str(strike),
        scenario_price=str(scenario_price),
        target_payoff_dollars=str(target_payoff_dollars),
        option_payoff_per_contract=str(option_payoff_per_contract),
        contracts=contracts_int,
    )

    return contracts_int
