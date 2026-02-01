"""Business Unit: hedge_executor | Status: current.

Option contract selector for hedge execution.

Queries option chains and selects optimal contracts based on
delta targets, DTE requirements, and liquidity filters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from the_alchemiser.shared.errors import TradingClientError
from the_alchemiser.shared.errors.exceptions import NoLiquidContractsError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.adapters import AlpacaOptionsAdapter
from the_alchemiser.shared.options.constants import (
    LIMIT_PRICE_DISCOUNT_FACTOR,
    LIQUIDITY_FILTERS,
    STRIKE_MAX_OTM_RATIO,
    STRIKE_MIN_OTM_RATIO,
    TAIL_HEDGE_TEMPLATE,
)
from the_alchemiser.shared.options.convexity_selector import ConvexitySelector
from the_alchemiser.shared.options.schemas import OptionContract, OptionType
from the_alchemiser.shared.options.tenor_selector import TenorSelector
from the_alchemiser.shared.options.utils import calculate_contracts_for_payoff_target

logger = get_logger(__name__)


@dataclass(frozen=True)
class SelectedOption:
    """Selected option contract for execution."""

    contract: OptionContract
    contracts_to_buy: int
    estimated_premium: Decimal
    limit_price: Decimal


@dataclass(frozen=True)
class SelectedSpread:
    """Selected spread contracts for execution (both legs)."""

    long_leg: OptionContract
    short_leg: OptionContract
    contracts_to_buy: int
    estimated_net_premium: Decimal  # Net premium (long - short credit)
    long_limit_price: Decimal
    short_limit_price: Decimal


class OptionSelector:
    """Selects optimal option contracts for hedging.

    Queries option chains and filters by:
    - Target delta (e.g., 15-delta for tail hedges)
    - Target DTE (e.g., 90 days)
    - Liquidity (open interest, bid-ask spread)
    """

    def __init__(self, options_adapter: AlpacaOptionsAdapter) -> None:
        """Initialize option selector.

        Args:
            options_adapter: Alpaca options API adapter

        """
        self._adapter = options_adapter
        self._template = TAIL_HEDGE_TEMPLATE
        self._filters = LIQUIDITY_FILTERS
        self._tenor_selector = TenorSelector()
        self._convexity_selector = ConvexitySelector()

    def select_hedge_contract(
        self,
        underlying_symbol: str,
        target_delta: Decimal,
        target_dte: int,
        premium_budget: Decimal,
        underlying_price: Decimal,
        nav: Decimal | None = None,
        correlation_id: str | None = None,
        current_vix: Decimal | None = None,
        iv_percentile: Decimal | None = None,
    ) -> SelectedOption | None:
        """Select optimal option contract for hedging.

        Args:
            underlying_symbol: Underlying ETF symbol (QQQ, SPY)
            target_delta: Target put delta (e.g., 0.15)
            target_dte: Target days to expiry
            premium_budget: Dollar amount available for premium
            underlying_price: Current underlying price
            nav: Portfolio NAV (optional, for payoff-based sizing)
            correlation_id: Correlation ID for tracing
            current_vix: Current VIX level (optional, enables dynamic tenor)
            iv_percentile: IV percentile (optional, for tenor selection)

        Returns:
            SelectedOption if found, None if no suitable contract

        Raises:
            NoLiquidContractsError: If no contracts pass liquidity filters (fail-closed)

        """
        # Use dynamic tenor selection if VIX provided
        effective_max_dte = self._filters.max_dte
        if current_vix is not None:
            tenor_recommendation = self._tenor_selector.select_tenor(
                current_vix=current_vix,
                iv_percentile=iv_percentile,
                use_ladder=False,  # For now, use single tenor
            )
            target_dte = tenor_recommendation.primary_dte
            # Ensure query window includes dynamically selected tenor
            # This prevents longer-tenor recommendations from being excluded
            effective_max_dte = max(self._filters.max_dte, target_dte + 15)
            logger.info(
                "Dynamic tenor selected",
                target_dte=target_dte,
                effective_max_dte=effective_max_dte,
                rationale=tenor_recommendation.rationale,
            )

        logger.info(
            "Selecting hedge contract",
            underlying=underlying_symbol,
            target_delta=str(target_delta),
            target_dte=target_dte,
            premium_budget=str(premium_budget),
            correlation_id=correlation_id,
        )

        # Calculate expiration date range
        today = datetime.now(UTC).date()
        min_expiry = today + timedelta(days=self._filters.min_dte)
        max_expiry = today + timedelta(days=effective_max_dte)

        # Target expiry around target_dte
        target_expiry = today + timedelta(days=target_dte)

        # Calculate strike range (OTM puts)
        # MAX: Maximum strike (closest to ATM) - for reasonable delta
        # MIN: Minimum strike (furthest OTM) - for tail protection
        strike_max = underlying_price * STRIKE_MAX_OTM_RATIO
        strike_min = underlying_price * STRIKE_MIN_OTM_RATIO

        try:
            # Query option chain
            contracts = self._adapter.get_option_chain(
                underlying_symbol=underlying_symbol,
                expiration_date_gte=min_expiry,
                expiration_date_lte=max_expiry,
                strike_price_gte=strike_min,
                strike_price_lte=strike_max,
                option_type=OptionType.PUT,
                limit=200,
            )

            if not contracts:
                # No contracts returned from adapter - likely an API/data issue
                logger.error(
                    "No contracts found in option chain - API/data issue",
                    underlying=underlying_symbol,
                    correlation_id=correlation_id,
                    alert_required=True,
                )
                # Return None to indicate adapter/API error (not fail-closed)
                # Caller can decide whether to fail closed or retry
                return None

            # Pre-filter by DTE before fetching quotes (reduce quote API calls)
            dte_filtered = [
                c
                for c in contracts
                if self._filters.min_dte <= c.days_to_expiry <= effective_max_dte
            ]

            if not dte_filtered:
                logger.warning(
                    "No contracts in DTE range",
                    underlying=underlying_symbol,
                    min_dte=self._filters.min_dte,
                    max_dte=self._filters.max_dte,
                )
                return None

            # Fetch quotes for filtered contracts (contracts endpoint doesn't return quotes)
            symbols = [c.symbol for c in dte_filtered]
            quotes = self._adapter.get_option_quotes_batch(symbols)

            # Enrich contracts with quote data
            enriched_contracts = []
            for contract in dte_filtered:
                quote = quotes.get(contract.symbol)
                if quote:
                    # Create new contract with quote data
                    enriched = OptionContract(
                        symbol=contract.symbol,
                        underlying_symbol=contract.underlying_symbol,
                        option_type=contract.option_type,
                        strike_price=contract.strike_price,
                        expiration_date=contract.expiration_date,
                        bid_price=quote.get("bid_price"),
                        ask_price=quote.get("ask_price"),
                        last_price=contract.last_price,
                        volume=contract.volume,
                        open_interest=contract.open_interest,
                        delta=contract.delta,
                        gamma=contract.gamma,
                        theta=contract.theta,
                        vega=contract.vega,
                        implied_volatility=contract.implied_volatility,
                    )
                    enriched_contracts.append(enriched)
                else:
                    # Keep original contract (may fail liquidity filter)
                    enriched_contracts.append(contract)

            logger.info(
                "Enriched contracts with quotes",
                underlying=underlying_symbol,
                total_contracts=len(dte_filtered),
                contracts_with_quotes=len(quotes),
            )

            contracts = enriched_contracts

            if not contracts:
                return None

            # Filter and score contracts
            best_contract = self._find_best_contract(
                contracts=contracts,
                target_delta=target_delta,
                target_expiry=target_expiry,
                underlying_price=underlying_price,
            )

            if best_contract is None:
                # FAIL CLOSED: No contracts passed liquidity filters
                logger.error(
                    "No contract passed liquidity filters - FAILING CLOSED",
                    underlying=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                    fail_closed_condition="no_liquid_contracts",
                    alert_required=True,
                )
                raise NoLiquidContractsError(
                    message=f"No option contracts passed liquidity filters for {underlying_symbol}. Checked {len(contracts)} contracts. Cannot execute hedge with illiquid options.",
                    underlying_symbol=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                )

            # Calculate contracts to buy and limit price
            return self._build_selected_option(
                contract=best_contract,
                premium_budget=premium_budget,
                underlying_price=underlying_price,
                target_delta=target_delta,
                nav=nav,
            )

        except NoLiquidContractsError:
            # Re-raise fail-closed errors
            raise
        except TradingClientError as e:
            # API/broker errors - log and return None to allow caller to handle
            logger.error(
                "Trading API error selecting hedge contract",
                underlying=underlying_symbol,
                error=str(e),
                exc_info=True,
                correlation_id=correlation_id,
            )
            return None

    def _find_best_contract(
        self,
        contracts: list[OptionContract],
        target_delta: Decimal,
        target_expiry: date,
        underlying_price: Decimal,
    ) -> OptionContract | None:
        """Find best contract from chain based on delta and expiry.

        Uses convexity-based selection when sufficient data available,
        otherwise falls back to delta/expiry scoring.

        Args:
            contracts: List of option contracts
            target_delta: Target delta (positive, e.g., 0.15)
            target_expiry: Target expiration date
            underlying_price: Current underlying price

        Returns:
            Best matching contract, or None if none pass filters

        """
        # First pass: try with full filters
        best_contract = self._select_best_contract(
            contracts, target_delta, target_expiry, underlying_price, skip_oi_filter=False
        )

        if best_contract is not None:
            return best_contract

        # Check if ALL contracts have 0 open_interest (paper API limitation)
        all_zero_oi = all(c.open_interest == 0 for c in contracts)
        if all_zero_oi and contracts:
            logger.warning(
                "All contracts have 0 open_interest, skipping OI filter (paper API)",
                contracts_count=len(contracts),
            )
            # Second pass: retry without OI filter for paper trading
            best_contract = self._select_best_contract(
                contracts, target_delta, target_expiry, underlying_price, skip_oi_filter=True
            )

        return best_contract

    def _select_best_contract(
        self,
        contracts: list[OptionContract],
        target_delta: Decimal,
        target_expiry: date,
        underlying_price: Decimal,
        *,
        skip_oi_filter: bool,
    ) -> OptionContract | None:
        """Select best contract with optional filter bypass.

        Uses convexity-based selection when gamma data is available,
        otherwise falls back to delta/expiry scoring.

        Args:
            contracts: List of option contracts
            target_delta: Target delta
            target_expiry: Target expiration date
            underlying_price: Current underlying price
            skip_oi_filter: Skip open interest filter (for paper API)

        Returns:
            Best matching contract, or None if none pass filters

        """
        # Filter by liquidity first
        liquid_contracts = [
            c for c in contracts if self._passes_liquidity_filter(c, skip_oi_filter=skip_oi_filter)
        ]

        if not liquid_contracts:
            return None

        # Try convexity-based selection if gamma data available
        convexity_metrics = []
        for contract in liquid_contracts:
            metrics = self._convexity_selector.calculate_convexity_metrics(
                contract, underlying_price
            )
            if metrics is not None:
                convexity_metrics.append(metrics)

        # If we have sufficient convexity data, use it
        # Require non-empty AND at least half of contracts have gamma data
        min_required = max(1, len(liquid_contracts) // 2)
        if convexity_metrics and len(convexity_metrics) >= min_required:
            logger.info(
                "Using convexity-based selection",
                total_contracts=len(liquid_contracts),
                with_convexity=len(convexity_metrics),
            )

            # Filter by payoff contribution
            filtered_metrics = self._convexity_selector.filter_by_payoff_contribution(
                convexity_metrics
            )

            if filtered_metrics:
                # Rank by convexity and return best
                ranked = self._convexity_selector.rank_by_convexity(filtered_metrics)
                return ranked[0].contract

        # Fallback: traditional delta/expiry scoring
        logger.info(
            "Using traditional delta/expiry scoring",
            total_contracts=len(liquid_contracts),
            with_convexity=len(convexity_metrics),
        )

        best_contract: OptionContract | None = None
        best_score = Decimal("999999")

        for contract in liquid_contracts:
            # Score contract (lower is better)
            score = self._score_contract(contract, target_delta, target_expiry)

            if score < best_score:
                best_score = score
                best_contract = contract

        return best_contract

    def _passes_liquidity_filter(
        self, contract: OptionContract, *, skip_oi_filter: bool = False
    ) -> bool:
        """Check if contract passes liquidity requirements.

        Args:
            contract: Option contract to check
            skip_oi_filter: Skip open interest check (for paper API)

        Returns:
            True if contract passes all liquidity filters

        """
        # Check open interest (skip if OI data unavailable in paper API)
        if not skip_oi_filter and contract.open_interest < self._filters.min_open_interest:
            return False

        # Check volume
        if contract.volume < self._filters.min_volume:
            return False

        # Check mid price minimum (avoid penny options)
        mid_price = contract.mid_price
        if mid_price is None or mid_price < self._filters.min_mid_price:
            return False

        # Check bid-ask spread (percentage)
        spread_pct = contract.spread_pct
        if spread_pct is not None and spread_pct > self._filters.max_spread_pct:
            return False

        # Check absolute bid-ask spread
        if contract.bid_price is not None and contract.ask_price is not None:
            spread_absolute = contract.ask_price - contract.bid_price
            if spread_absolute > self._filters.max_spread_absolute:
                return False

        # Check DTE
        dte = contract.days_to_expiry
        if dte < self._filters.min_dte or dte > self._filters.max_dte:
            return False

        # Must have bid and ask
        return contract.bid_price is not None and contract.ask_price is not None

    def _score_contract(
        self,
        contract: OptionContract,
        target_delta: Decimal,
        target_expiry: date,
    ) -> Decimal:
        """Score contract based on how well it matches targets.

        Lower score is better. Considers:
        - Delta deviation from target
        - Expiry deviation from target
        - Spread (tighter is better)

        Args:
            contract: Option contract to score
            target_delta: Target delta
            target_expiry: Target expiration date

        Returns:
            Score (lower is better)

        """
        score = Decimal("0")

        # Delta deviation (weighted heavily)
        if contract.delta is not None:
            delta_diff = abs(abs(contract.delta) - target_delta)
            score += delta_diff * 100
        else:
            # Estimate delta from strike/price if not available
            # Penalize contracts without delta data
            score += Decimal("10")

        # Expiry deviation (days)
        expiry_diff = abs((contract.expiration_date - target_expiry).days)
        score += Decimal(str(expiry_diff))

        # Spread penalty
        spread_pct = contract.spread_pct
        if spread_pct is not None:
            score += spread_pct * 50

        return score

    def _build_selected_option(
        self,
        contract: OptionContract,
        premium_budget: Decimal,
        underlying_price: Decimal,
        target_delta: Decimal,
        nav: Decimal | None = None,
    ) -> SelectedOption:
        """Build SelectedOption with contract count and limit price.

        Uses scenario-payoff based sizing when NAV is provided, otherwise
        falls back to simple budget-based sizing.

        Args:
            contract: Selected option contract
            premium_budget: Available budget for premium
            underlying_price: Current underlying price
            target_delta: Target delta for the option
            nav: Portfolio NAV (optional, enables payoff-based sizing)

        Returns:
            SelectedOption with execution details

        """
        mid_price = contract.mid_price
        if mid_price is None or mid_price <= 0:
            mid_price = contract.ask_price or Decimal("1")

        # Calculate limit price (slightly better than mid for limit order)
        # For buying puts, we want to pay less than mid
        limit_price = mid_price * LIMIT_PRICE_DISCOUNT_FACTOR

        # Premium per contract = price * 100 shares
        premium_per_contract = mid_price * 100

        # Calculate contracts to buy
        contracts_to_buy = 1

        if nav is not None:
            # Use scenario-payoff based sizing
            # Default scenario from tail hedge template: -20% move
            scenario_move = self._template.scenario_move
            # Target payoff: use midpoint of min/max range
            target_payoff_pct = (
                self._template.min_payoff_nav_pct + self._template.max_payoff_nav_pct
            ) / Decimal("2")

            # Calculate contracts for target payoff
            contracts_by_payoff = calculate_contracts_for_payoff_target(
                underlying_price=underlying_price,
                option_delta=target_delta,
                scenario_move=scenario_move,
                target_payoff=target_payoff_pct,
                nav=nav,
            )

            # Apply budget cap
            max_contracts_by_budget = 1
            if premium_per_contract > 0:
                max_contracts_by_budget = int(premium_budget / premium_per_contract)

            # Use the smaller of payoff-based and budget-capped contracts
            contracts_to_buy = max(1, min(contracts_by_payoff, max_contracts_by_budget))

            logger.info(
                "Applied payoff-based sizing with budget cap",
                contracts_by_payoff=contracts_by_payoff,
                max_contracts_by_budget=max_contracts_by_budget,
                final_contracts=contracts_to_buy,
                scenario_move=str(scenario_move),
                target_payoff_pct=str(target_payoff_pct),
            )
        else:
            # Fallback to simple budget-based sizing
            if premium_per_contract > 0:
                contracts_to_buy = max(1, int(premium_budget / premium_per_contract))

        # Estimated total premium
        estimated_premium = premium_per_contract * contracts_to_buy

        logger.info(
            "Selected option contract",
            symbol=contract.symbol,
            strike=str(contract.strike_price),
            expiry=contract.expiration_date.isoformat(),
            delta=str(contract.delta) if contract.delta else "N/A",
            mid_price=str(mid_price),
            limit_price=str(limit_price),
            contracts=contracts_to_buy,
            estimated_premium=str(estimated_premium),
        )

        return SelectedOption(
            contract=contract,
            contracts_to_buy=contracts_to_buy,
            estimated_premium=estimated_premium,
            limit_price=limit_price,
        )

    def select_spread_contracts(
        self,
        underlying_symbol: str,
        long_delta: Decimal,
        short_delta: Decimal,
        target_dte: int,
        premium_budget: Decimal,
        underlying_price: Decimal,
        nav: Decimal | None = None,
        correlation_id: str | None = None,
    ) -> SelectedSpread | None:
        """Select optimal spread contracts (long and short legs).

        Args:
            underlying_symbol: Underlying ETF symbol (QQQ, SPY)
            long_delta: Target delta for long leg (e.g., 0.30)
            short_delta: Target delta for short leg (e.g., 0.10)
            target_dte: Target days to expiry
            premium_budget: Dollar amount available for net premium
            underlying_price: Current underlying price
            nav: Portfolio NAV (optional, for payoff-based sizing)
            correlation_id: Correlation ID for tracing

        Returns:
            SelectedSpread if both legs found, None if either leg unavailable

        Raises:
            NoLiquidContractsError: If either leg fails liquidity filters (fail-closed)

        """
        logger.info(
            "Selecting spread contracts",
            underlying=underlying_symbol,
            long_delta=str(long_delta),
            short_delta=str(short_delta),
            target_dte=target_dte,
            premium_budget=str(premium_budget),
            correlation_id=correlation_id,
        )

        # Calculate expiration date range
        today = datetime.now(UTC).date()
        min_expiry = today + timedelta(days=self._filters.min_dte)
        max_expiry = today + timedelta(days=self._filters.max_dte)
        target_expiry = today + timedelta(days=target_dte)

        # Calculate strike range (OTM puts)
        strike_max = underlying_price * STRIKE_MAX_OTM_RATIO
        strike_min = underlying_price * STRIKE_MIN_OTM_RATIO

        try:
            # Query option chain (same for both legs)
            contracts = self._adapter.get_option_chain(
                underlying_symbol=underlying_symbol,
                expiration_date_gte=min_expiry,
                expiration_date_lte=max_expiry,
                strike_price_gte=strike_min,
                strike_price_lte=strike_max,
                option_type=OptionType.PUT,
                limit=200,
            )

            if not contracts:
                logger.error(
                    "No contracts found in option chain for spread - API/data issue",
                    underlying=underlying_symbol,
                    correlation_id=correlation_id,
                    alert_required=True,
                )
                return None

            # Pre-filter by DTE
            dte_filtered = [
                c
                for c in contracts
                if self._filters.min_dte <= c.days_to_expiry <= self._filters.max_dte
            ]

            if not dte_filtered:
                logger.warning(
                    "No contracts in DTE range for spread",
                    underlying=underlying_symbol,
                    min_dte=self._filters.min_dte,
                    max_dte=self._filters.max_dte,
                )
                return None

            # Fetch quotes for filtered contracts
            symbols = [c.symbol for c in dte_filtered]
            quotes = self._adapter.get_option_quotes_batch(symbols)

            # Enrich contracts with quote data
            enriched_contracts = []
            for contract in dte_filtered:
                quote = quotes.get(contract.symbol)
                if quote:
                    enriched = OptionContract(
                        symbol=contract.symbol,
                        underlying_symbol=contract.underlying_symbol,
                        option_type=contract.option_type,
                        strike_price=contract.strike_price,
                        expiration_date=contract.expiration_date,
                        bid_price=quote.get("bid_price"),
                        ask_price=quote.get("ask_price"),
                        last_price=contract.last_price,
                        volume=contract.volume,
                        open_interest=contract.open_interest,
                        delta=contract.delta,
                        gamma=contract.gamma,
                        theta=contract.theta,
                        vega=contract.vega,
                        implied_volatility=contract.implied_volatility,
                    )
                    enriched_contracts.append(enriched)
                else:
                    enriched_contracts.append(contract)

            contracts = enriched_contracts

            if not contracts:
                return None

            # Select long leg (higher delta, e.g., 30-delta)
            long_leg = self._find_best_contract(
                contracts=contracts,
                target_delta=long_delta,
                target_expiry=target_expiry,
            )

            if long_leg is None:
                logger.error(
                    "No liquid contract found for long leg - FAILING CLOSED",
                    underlying=underlying_symbol,
                    long_delta=str(long_delta),
                    correlation_id=correlation_id,
                    fail_closed_condition="no_liquid_long_leg",
                    alert_required=True,
                )
                raise NoLiquidContractsError(
                    message=f"No liquid contract found for long leg ({long_delta} delta) on {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                )

            # Select short leg (lower delta, e.g., 10-delta)
            short_leg = self._find_best_contract(
                contracts=contracts,
                target_delta=short_delta,
                target_expiry=target_expiry,
            )

            if short_leg is None:
                logger.error(
                    "No liquid contract found for short leg - FAILING CLOSED",
                    underlying=underlying_symbol,
                    short_delta=str(short_delta),
                    correlation_id=correlation_id,
                    fail_closed_condition="no_liquid_short_leg",
                    alert_required=True,
                )
                raise NoLiquidContractsError(
                    message=f"No liquid contract found for short leg ({short_delta} delta) on {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                )

            # Calculate pricing for both legs - fail closed if no valid price
            long_mid_price = long_leg.mid_price or long_leg.ask_price
            if long_mid_price is None or long_mid_price <= 0:
                logger.error(
                    "No valid price for long leg - FAILING CLOSED",
                    underlying=underlying_symbol,
                    long_symbol=long_leg.symbol,
                    correlation_id=correlation_id,
                    fail_closed_condition="no_valid_long_leg_price",
                    alert_required=True,
                )
                raise NoLiquidContractsError(
                    message=f"No valid price for long leg {long_leg.symbol} on {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                )

            short_mid_price = short_leg.mid_price or short_leg.bid_price
            if short_mid_price is None or short_mid_price <= 0:
                logger.error(
                    "No valid price for short leg - FAILING CLOSED",
                    underlying=underlying_symbol,
                    short_symbol=short_leg.symbol,
                    correlation_id=correlation_id,
                    fail_closed_condition="no_valid_short_leg_price",
                    alert_required=True,
                )
                raise NoLiquidContractsError(
                    message=f"No valid price for short leg {short_leg.symbol} on {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                )

            # Net debit = long premium - short credit
            net_debit_per_contract = (long_mid_price - short_mid_price) * 100

            # Validate spread pricing - must be a net debit for protective put spreads
            if net_debit_per_contract <= 0:
                logger.error(
                    "Invalid spread pricing - net debit must be positive for protective spread - FAILING CLOSED",
                    underlying=underlying_symbol,
                    long_strike=str(long_leg.strike_price),
                    long_mid_price=str(long_mid_price),
                    short_strike=str(short_leg.strike_price),
                    short_mid_price=str(short_mid_price),
                    net_debit=str(net_debit_per_contract),
                    correlation_id=correlation_id,
                    fail_closed_condition="invalid_spread_pricing",
                    alert_required=True,
                )
                raise NoLiquidContractsError(
                    message=f"Invalid spread pricing on {underlying_symbol}: net debit {net_debit_per_contract} <= 0. "
                    "Long leg premium must exceed short leg premium for protective put spread.",
                    underlying_symbol=underlying_symbol,
                    contracts_checked=len(contracts),
                    correlation_id=correlation_id,
                )

            # Calculate contracts to buy based on net premium budget
            contracts_to_buy = max(1, int(premium_budget / net_debit_per_contract))

            # Estimated net premium
            estimated_net_premium = net_debit_per_contract * contracts_to_buy

            # Limit prices for each leg
            long_limit_price = long_mid_price * LIMIT_PRICE_DISCOUNT_FACTOR
            short_limit_price = short_mid_price * (Decimal("2") - LIMIT_PRICE_DISCOUNT_FACTOR)

            logger.info(
                "Selected spread contracts",
                underlying=underlying_symbol,
                long_symbol=long_leg.symbol,
                long_strike=str(long_leg.strike_price),
                long_delta=str(long_leg.delta) if long_leg.delta else "N/A",
                short_symbol=short_leg.symbol,
                short_strike=str(short_leg.strike_price),
                short_delta=str(short_leg.delta) if short_leg.delta else "N/A",
                contracts=contracts_to_buy,
                net_debit=str(net_debit_per_contract),
                estimated_net_premium=str(estimated_net_premium),
            )

            return SelectedSpread(
                long_leg=long_leg,
                short_leg=short_leg,
                contracts_to_buy=contracts_to_buy,
                estimated_net_premium=estimated_net_premium,
                long_limit_price=long_limit_price,
                short_limit_price=short_limit_price,
            )

        except NoLiquidContractsError:
            # Re-raise fail-closed errors
            raise
        except TradingClientError as e:
            # API/broker errors - log and return None to allow caller to handle
            logger.error(
                "Trading API error selecting spread contracts",
                underlying=underlying_symbol,
                error=str(e),
                exc_info=True,
                correlation_id=correlation_id,
            )
            return None
