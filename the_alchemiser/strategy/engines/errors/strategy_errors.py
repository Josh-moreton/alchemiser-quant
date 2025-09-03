"""Business Unit: strategy | Status: current..__init__(message)
        self.strategy_name = strategy_name


class StrategyComputationError(Exception):
    """Raised when strategy computation fails."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        super().__init__(message)
        self.strategy_name = strategy_name


class StrategyExecutionError(Exception):
    """Raised when strategy execution fails."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        super().__init__(message)
        self.strategy_name = strategy_name


class MarketDataUnavailableError(Exception):
    """Raised when required market data is unavailable."""

    def __init__(self, message: str, symbols: list[str] | None = None) -> None:
        super().__init__(message)
        self.symbols = symbols or []
