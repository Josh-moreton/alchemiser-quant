"""Business Unit: strategy | Status: current..

        Args:
            market_data_port: Market data access interface
            strategy_allocations: Optional strategy allocations (defaults from registry)

        """
        self.market_data_port = market_data_port
        self.logger = logging.getLogger(__name__)

        # Use provided allocations or defaults from registry
        if strategy_allocations is None:
            self.strategy_allocations = StrategyRegistry.get_default_allocations()
        else:
            # Filter to only enabled strategies
            self.strategy_allocations = {
                strategy_type: allocation
                for strategy_type, allocation in strategy_allocations.items()
                if StrategyRegistry.is_strategy_enabled(strategy_type)
            }

        # Validate allocations sum to 1.0
        total_allocation = sum(self.strategy_allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Strategy allocations must sum to 1.0, got {total_allocation}")

        # Initialize typed strategy engines
        self.strategy_engines: dict[StrategyType, StrategyEngine] = {}
        self._initialize_typed_engines()

        self.logger.info(
            f"TypedStrategyManager initialized with allocations: {self.strategy_allocations}"
        )

    def _initialize_typed_engines(self) -> None:
        """Initialize typed strategy engines that implement StrategyEngine protocol."""
        for strategy_type in self.strategy_allocations:
            try:
                engine = self._create_typed_engine(strategy_type)
                self.strategy_engines[strategy_type] = engine
                self.logger.info(
                    f"Initialized {strategy_type.value} typed engine with "
                    f"{self.strategy_allocations[strategy_type]:.1%} allocation"
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize {strategy_type.value} typed engine: {e}")
                # Remove from allocations if initialization failed
                del self.strategy_allocations[strategy_type]

    def _create_typed_engine(self, strategy_type: StrategyType) -> StrategyEngine:
        """Create typed strategy engine instance."""
        if strategy_type == StrategyType.NUCLEAR:
            return NuclearTypedEngine(self.market_data_port)
        if strategy_type == StrategyType.KLM:
            return TypedKLMStrategyEngine(self.market_data_port)
        if strategy_type == StrategyType.TECL:
            from .tecl_strategy_engine import TECLStrategyEngine

            return TECLStrategyEngine(self.market_data_port)
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    def generate_all_signals(self, timestamp: datetime | None = None) -> AggregatedSignals:
        """Generate signals from all enabled strategies.

        Args:
            timestamp: Optional timestamp for signal generation (defaults to now)

        Returns:
            AggregatedSignals containing all strategy signals and aggregation results

        Raises:
            StrategyExecutionError: If signal generation fails

        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        aggregated = AggregatedSignals()

        # Generate signals from each strategy
        for strategy_type, engine in self.strategy_engines.items():
            try:
                self.logger.info(f"Generating signals from {strategy_type.value} strategy")

                if hasattr(engine, "generate_signals"):
                    # All engines now use new constructor injection interface
                    signals = engine.generate_signals(timestamp)
                else:
                    self.logger.warning(
                        f"{strategy_type.value} engine doesn't have generate_signals method"
                    )
                    signals = []

                # Validate signals
                if signals and hasattr(engine, "validate_signals"):
                    engine.validate_signals(signals)

                aggregated.add_strategy_signals(strategy_type, signals)
                self.logger.info(f"{strategy_type.value} generated {len(signals)} signals")

            except Exception as e:
                # Log error and skip this strategy
                self.logger.error(f"Error generating signals for {strategy_type.value}: {e}")
                # Continue with other strategies
                aggregated.add_strategy_signals(strategy_type, [])
                continue

        # Perform aggregation and conflict resolution
        self._aggregate_signals(aggregated)

        return aggregated

    def _aggregate_signals(self, aggregated: AggregatedSignals) -> None:
        """Aggregate signals from multiple strategies and resolve conflicts.

        Args:
            aggregated: AggregatedSignals object to populate with consolidated results

        """
        # Group signals by symbol
        signals_by_symbol: dict[str, list[tuple[StrategyType, StrategySignal]]] = {}

        for strategy_type, signals in aggregated.signals_by_strategy.items():
            for signal in signals:
                symbol_str = signal.symbol.value
                if symbol_str not in signals_by_symbol:
                    signals_by_symbol[symbol_str] = []
                signals_by_symbol[symbol_str].append((strategy_type, signal))

        # Process each symbol
        for symbol_str, strategy_signals in signals_by_symbol.items():
            if len(strategy_signals) == 1:
                # No conflict - use the single signal
                _, signal = strategy_signals[0]
                aggregated.consolidated_signals.append(signal)
            else:
                # Multiple strategies have opinions on this symbol - resolve conflict
                resolved_signal = self._resolve_signal_conflict(symbol_str, strategy_signals)
                if resolved_signal:
                    aggregated.consolidated_signals.append(resolved_signal)

                # Record the conflict for analysis
                conflict = {
                    "symbol": symbol_str,
                    "strategies": [strategy.value for strategy, _ in strategy_signals],
                    "actions": [signal.action for _, signal in strategy_signals],
                    "confidences": [
                        float(signal.confidence.value) for _, signal in strategy_signals
                    ],
                    "resolution": resolved_signal.action if resolved_signal else "NO_ACTION",
                }
                aggregated.conflicts.append(conflict)

    def _resolve_signal_conflict(
        self, symbol: str, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> StrategySignal | None:
        """Resolve conflicts when multiple strategies have different opinions on the same symbol.

        Args:
            symbol: The symbol with conflicting signals
            strategy_signals: List of (strategy_type, signal) tuples

        Returns:
            Resolved StrategySignal or None if no resolution possible

        """
        self.logger.info(f"Resolving conflict for {symbol} with {len(strategy_signals)} signals")

        # Conflict resolution strategy:
        # 1. If all actions are the same, combine with weighted confidence
        # 2. If actions differ, use highest confidence signal
        # 3. Weight by strategy allocation

        actions = [signal.action for _, signal in strategy_signals]
        unique_actions = set(actions)

        if len(unique_actions) == 1:
            # All strategies agree on action - combine confidences
            return self._combine_agreeing_signals(symbol, strategy_signals)
        # Strategies disagree - use highest weighted confidence
        return self._select_highest_confidence_signal(symbol, strategy_signals)

    def _combine_agreeing_signals(
        self, symbol: str, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> StrategySignal:
        """Combine signals when all strategies agree on the action."""
        # Use the first signal as template
        _, template_signal = strategy_signals[0]

        # Calculate weighted confidence
        total_weighted_confidence = Decimal("0")
        total_weight = Decimal("0")
        combined_reasoning = f"Combined signal for {symbol}:\n"

        for strategy_type, signal in strategy_signals:
            weight = Decimal(str(self.strategy_allocations[strategy_type]))
            confidence_value = signal.confidence.value
            weighted_confidence = confidence_value * weight

            total_weighted_confidence += weighted_confidence
            total_weight += weight

            combined_reasoning += f"• {strategy_type.value}: {signal.action} (confidence: {confidence_value:.2f}, weight: {weight:.1%})\n"

        # Average confidence weighted by strategy allocation
        final_confidence = (
            total_weighted_confidence / total_weight if total_weight > 0 else Decimal("0.5")
        )

        combined_reasoning += f"• Final confidence: {final_confidence:.2f} (weighted average)"

        return StrategySignal(
            symbol=Symbol(symbol),
            action=template_signal.action,
            confidence=Confidence(final_confidence),
            target_allocation=template_signal.target_allocation,
            reasoning=combined_reasoning,
            timestamp=template_signal.timestamp,
        )

    def _select_highest_confidence_signal(
        self, symbol: str, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> StrategySignal:
        """Select signal with highest weighted confidence when strategies disagree."""
        best_score = Decimal("-1")
        best_signal = None
        best_strategy = None

        reasoning = f"Conflict resolution for {symbol}:\n"

        for strategy_type, signal in strategy_signals:
            weight = Decimal(str(self.strategy_allocations[strategy_type]))
            confidence_value = signal.confidence.value
            weighted_score = confidence_value * weight

            reasoning += f"• {strategy_type.value}: {signal.action} (confidence: {confidence_value:.2f}, weight: {weight:.1%}, score: {weighted_score:.3f})\n"

            if weighted_score > best_score:
                best_score = weighted_score
                best_signal = signal
                best_strategy = strategy_type

        if best_signal is None or best_strategy is None:
            # Fallback - shouldn't happen but be safe
            _, best_signal = strategy_signals[0]
            best_strategy = strategy_signals[0][0]

        reasoning += f"• Winner: {best_strategy.value} with weighted score {best_score:.3f}"

        # Create new signal with combined reasoning
        return StrategySignal(
            symbol=best_signal.symbol,
            action=best_signal.action,
            confidence=best_signal.confidence,
            target_allocation=best_signal.target_allocation,
            reasoning=reasoning,
            timestamp=best_signal.timestamp,
        )

    def get_strategy_allocations(self) -> dict[StrategyType, float]:
        """Get current strategy allocations."""
        return self.strategy_allocations.copy()

    def get_enabled_strategies(self) -> list[StrategyType]:
        """Get list of enabled strategy types."""
        return list(self.strategy_engines.keys())

    # ==================== NEW DTO-BASED METHODS ====================

    def generate_signals_dto(
        self, timestamp: datetime | None = None, correlation_id: str | None = None
    ) -> list[StrategySignalDTO]:
        """Generate strategy signals and return as DTOs for inter-module communication.

        This method provides the same functionality as generate_signals() but returns
        StrategySignalDTO objects suitable for communication with other modules.

        Args:
            timestamp: Optional timestamp for signal generation
            correlation_id: Optional correlation ID for tracking

        Returns:
            List of StrategySignalDTO objects

        Raises:
            StrategyExecutionError: If signal generation fails

        """
        # Import at runtime to avoid circular imports
        from the_alchemiser.shared.adapters import batch_strategy_signals_to_dtos

        # Generate signals using existing method
        aggregated_signals = self.generate_signals(timestamp)

        # Convert to DTOs using adapters
        if not aggregated_signals.consolidated_signals:
            return []

        return batch_strategy_signals_to_dtos(
            signals=aggregated_signals.consolidated_signals,
            base_correlation_id=correlation_id,
            strategy_name="typed_strategy_manager",
        )

    def get_signals_by_strategy_dto(
        self, timestamp: datetime | None = None, correlation_id: str | None = None
    ) -> dict[str, list[StrategySignalDTO]]:
        """Get signals grouped by strategy as DTOs.

        Args:
            timestamp: Optional timestamp for signal generation
            correlation_id: Optional correlation ID for tracking

        Returns:
            Dictionary mapping strategy names to lists of StrategySignalDTO objects

        """
        # Import at runtime to avoid circular imports
        from the_alchemiser.shared.adapters import batch_strategy_signals_to_dtos

        # Generate signals using existing method
        aggregated_signals = self.generate_signals(timestamp)

        # Convert each strategy's signals to DTOs
        signals_by_strategy = {}
        for strategy_type, signals in aggregated_signals.signals_by_strategy.items():
            if signals:
                strategy_name = strategy_type.value
                signals_by_strategy[strategy_name] = batch_strategy_signals_to_dtos(
                    signals=signals,
                    base_correlation_id=correlation_id,
                    strategy_name=strategy_name,
                )
            else:
                signals_by_strategy[strategy_type.value] = []

        return signals_by_strategy

    def get_portfolio_context_dto(self) -> dict[str, Any]:
        """Get strategy manager context for portfolio module consumption.

        Returns:
            Dictionary with strategy context data suitable for portfolio module

        """
        return {
            "strategy_allocations": {
                strategy_type.value: allocation
                for strategy_type, allocation in self.strategy_allocations.items()
            },
            "enabled_strategies": [strategy.value for strategy in self.get_enabled_strategies()],
            "total_strategies": len(self.strategy_engines),
            "manager_type": "typed_strategy_manager",
        }
