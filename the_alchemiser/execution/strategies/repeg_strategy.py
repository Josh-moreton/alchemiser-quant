#!/usr/bin/env python3
"""Business Unit: execution | Status: current..config = config
        self.strategy_name = strategy_name
        # Require explicit service injection; if omitted, create a new instance (transitional)
        self._tick_size_service = tick_size_service or DynamicTickSizeService()

    def plan_attempts(self) -> list[AttemptPlan]:
        """Plan all attempts for a repeg sequence."""
        attempts: list[AttemptPlan] = []
        for attempt_index in range(self.config.max_attempts):
            timeout = self._calculate_timeout(attempt_index)
            attempts.append(
                AttemptPlan(
                    attempt_index=attempt_index,
                    timeout_seconds=timeout,
                    price_improvement_ticks=attempt_index * self.config.price_improvement_ticks,
                    reason=("initial" if attempt_index == 0 else f"repeg_{attempt_index}"),
                )
            )
        return attempts

    def next_attempt(self, previous_state: AttemptState, attempt_index: int) -> AttemptResult:
        """Calculate next attempt parameters."""
        timeout = self._calculate_timeout(attempt_index)
        price = self._calculate_price(previous_state, attempt_index)
        reason = (
            "initial_aggressive_limit" if attempt_index == 0 else f"repeg_attempt_{attempt_index}"
        )
        return AttemptResult(
            price=price,
            timeout_seconds=timeout,
            reason=reason,
            attempt_index=attempt_index,
        )

    def should_pause_for_volatility(
        self, original_spread_cents: Decimal, current_spread_cents: Decimal
    ) -> bool:
        if not self.config.enable_volatility_pause or original_spread_cents <= Decimal("0"):
            return False
        spread_degradation_pct = (
            current_spread_cents - original_spread_cents
        ) / original_spread_cents
        spread_degradation_bps = spread_degradation_pct * Decimal("10000")
        return spread_degradation_bps > self.config.volatility_pause_threshold_bps

    def _calculate_timeout(self, attempt_index: int) -> float:
        return self.config.base_timeout_seconds * (self.config.timeout_multiplier**attempt_index)

    def _quantize(self, price: Decimal, symbol: str) -> Decimal:
        """Quantize price to appropriate tick size using dynamic resolution.

        Phase 7 Enhancement: Uses DynamicTickSizeService instead of hardcoded tick_size.
        """
        # Get dynamic tick size based on symbol and current price
        tick = resolve_tick_size(self._tick_size_service, symbol, price)
        if tick <= Decimal("0"):
            return price
        # (price / tick) rounded then multiplied back
        steps = (price / tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return steps * tick

    def _calculate_price(self, state: AttemptState, attempt_index: int) -> Decimal:
        """Calculate price for attempt using dynamic tick size resolution."""
        # Get dynamic tick size for this symbol
        mid_price = (state.bid + state.ask) / 2
        dynamic_tick = resolve_tick_size(self._tick_size_service, state.symbol, mid_price)

        if not self.config.enable_adaptive_pricing:
            base_price = (
                state.ask + dynamic_tick
                if state.side == OrderSide.BUY
                else state.bid - dynamic_tick
            )
            return self._quantize(base_price, state.symbol)

        price_improvement = (
            Decimal(self.config.price_improvement_ticks) * dynamic_tick * Decimal(attempt_index)
        )
        if state.side == OrderSide.BUY:
            base_price = state.ask + dynamic_tick + price_improvement
        else:
            base_price = state.bid - dynamic_tick - price_improvement
        return self._quantize(base_price, state.symbol)
