#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Custom exception classes for The Alchemiser Quantitative Trading System.

This module defines specific exception types for different failure scenarios
to enable better error handling and debugging throughout the application.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class AlchemiserError(Exception):
    """Base exception class for all Alchemiser-specific errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize base error with optional contextual data."""
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class ConfigurationError(AlchemiserError):
    """Raised when there are configuration-related issues."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | int | float | bool | None = None,  # noqa: FBT001
    ) -> None:
        """Raise when configuration values are missing or invalid."""
        context = {}
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = str(config_value)  # Convert to string for safety
        super().__init__(message, context)
        self.config_key = config_key
        self.config_value = config_value


class DataProviderError(AlchemiserError):
    """Raised when data provider operations fail."""


class TradingClientError(AlchemiserError):
    """Raised when trading client operations fail."""


class OrderExecutionError(TradingClientError):
    """Raised when order placement or execution fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        account_id: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """Create an order execution error with contextual details."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if order_type:
            context["order_type"] = order_type
        if order_id:
            context["order_id"] = order_id
        if quantity is not None:
            context["quantity"] = quantity
        if price is not None:
            context["price"] = price
        if account_id:
            context["account_id"] = account_id
        if retry_count > 0:
            context["retry_count"] = retry_count

        super().__init__(message, context)
        self.symbol = symbol
        self.order_type = order_type
        self.order_id = order_id
        self.quantity = quantity
        self.price = price
        self.account_id = account_id
        self.retry_count = retry_count


class OrderPlacementError(OrderExecutionError):
    """Raised when order placement fails and returns None ID."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        reason: str | None = None,
    ) -> None:
        """Create an order placement error for None order ID scenarios."""
        super().__init__(
            message=message,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        self.reason = reason


class OrderTimeoutError(OrderExecutionError):
    """Raised when order execution times out during limit order sequence."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        timeout_seconds: float | None = None,
        attempt_number: int | None = None,
    ) -> None:
        """Create an order timeout error for re-pegging scenarios."""
        super().__init__(message=message, symbol=symbol, order_id=order_id)
        self.timeout_seconds = timeout_seconds
        self.attempt_number = attempt_number


class SpreadAnalysisError(DataProviderError):
    """Raised when spread analysis fails and cannot determine appropriate pricing."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        bid: float | None = None,
        ask: float | None = None,
        spread_cents: float | None = None,
    ) -> None:
        """Create a spread analysis error for pricing failures."""
        super().__init__(message)
        self.symbol = symbol
        self.bid = bid
        self.ask = ask
        self.spread_cents = spread_cents


class BuyingPowerError(OrderExecutionError):
    """Raised when insufficient buying power detected during execution."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        required_amount: float | None = None,
        available_amount: float | None = None,
        shortfall: float | None = None,
    ) -> None:
        """Create a buying power error with financial context."""
        super().__init__(message=message, symbol=symbol)
        self.required_amount = required_amount
        self.available_amount = available_amount
        self.shortfall = shortfall


class InsufficientFundsError(OrderExecutionError):
    """Raised when there are insufficient funds for an order."""


class PositionValidationError(TradingClientError):
    """Raised when position validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        requested_qty: float | None = None,
        available_qty: float | None = None,
    ) -> None:
        """Initialize position validation error."""
        super().__init__(message)
        self.symbol = symbol
        self.requested_qty = requested_qty
        self.available_qty = available_qty


class TemplateGenerationError(AlchemiserError):
    """Raised when email template generation fails."""

    def __init__(
        self,
        message: str,
        template_type: str | None = None,
        data_type: str | None = None,
    ) -> None:
        """Initialize template generation error.

        Args:
            message: Error message
            template_type: Type of template being generated (e.g., "signals", "portfolio")
            data_type: Type of data that caused the error (e.g., "signal", "indicators")

        """
        context = {}
        if template_type:
            context["template_type"] = template_type
        if data_type:
            context["data_type"] = data_type
        super().__init__(message, context)
        self.template_type = template_type
        self.data_type = data_type


class PortfolioError(AlchemiserError):
    """Raised when portfolio operations fail."""

    def __init__(
        self,
        message: str,
        module: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize portfolio error with context."""
        context: dict[str, Any] = {}
        if module:
            context["module"] = module
        if operation:
            context["operation"] = operation
        if correlation_id:
            context["correlation_id"] = correlation_id

        super().__init__(message, context)
        self.module = module
        self.operation = operation
        self.correlation_id = correlation_id


class NegativeCashBalanceError(PortfolioError):
    """Raised when account has negative or zero cash balance."""

    def __init__(
        self,
        message: str,
        cash_balance: str | None = None,
        module: str | None = None,
    ) -> None:
        """Initialize negative cash balance error with context."""
        super().__init__(message, module=module, operation="cash_balance_check")
        self.cash_balance = cash_balance


class IndicatorCalculationError(AlchemiserError):
    """Raised when technical indicator calculations fail."""

    def __init__(
        self, message: str, indicator_name: str | None = None, symbol: str | None = None
    ) -> None:
        """Raise when an indicator cannot be computed."""
        super().__init__(message)
        self.indicator_name = indicator_name
        self.symbol = symbol


class IndicatorError(AlchemiserError):
    """Raised when indicator service operations fail.

    This is used by the IndicatorLambdaClient when invoking the Indicators Lambda
    returns an error or fails.
    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        indicator_type: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Raise when indicator service operation fails.

        Args:
            message: Error message
            symbol: Symbol being processed
            indicator_type: Type of indicator that failed
            correlation_id: Correlation ID for tracing

        """
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if indicator_type:
            context["indicator_type"] = indicator_type
        if correlation_id:
            context["correlation_id"] = correlation_id

        super().__init__(message, context)
        self.symbol = symbol
        self.indicator_type = indicator_type
        self.correlation_id = correlation_id


class MarketDataError(DataProviderError):
    """Raised when market data retrieval fails."""

    def __init__(
        self, message: str, symbol: str | None = None, data_type: str | None = None
    ) -> None:
        """Raise when market data retrieval fails."""
        super().__init__(message)
        self.symbol = symbol
        self.data_type = data_type


class DataUnavailableError(MarketDataError):
    """Raised when historical data is unavailable from provider."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        required_start_date: str | None = None,
        required_end_date: str | None = None,
        available_start_date: str | None = None,
        available_end_date: str | None = None,
    ) -> None:
        """Initialize data unavailable error with date range context.

        Args:
            message: Error message
            symbol: Stock symbol
            required_start_date: Required start date (ISO format)
            required_end_date: Required end date (ISO format)
            available_start_date: Available start date from provider (ISO format)
            available_end_date: Available end date from provider (ISO format)

        """
        super().__init__(message, symbol=symbol, data_type="historical")
        self.required_start_date = required_start_date
        self.required_end_date = required_end_date
        self.available_start_date = available_start_date
        self.available_end_date = available_end_date


class ValidationError(AlchemiserError, ValueError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        value: str | int | float | None = None,
    ) -> None:
        """Create a validation error for invalid user data."""
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""

    def __init__(self, message: str, bucket: str | None = None, key: str | None = None) -> None:
        """Raise when interacting with Amazon S3 fails."""
        super().__init__(message)
        self.bucket = bucket
        self.key = key


class RateLimitError(AlchemiserError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Raise when API rate limit is exceeded."""
        super().__init__(message)
        self.retry_after = retry_after


class MarketClosedError(TradingClientError):
    """Raised when attempting to trade while markets are closed."""


class WebSocketError(DataProviderError):
    """Raised when WebSocket connection issues occur."""


class StreamingError(DataProviderError):
    """Raised when streaming data issues occur."""


class LoggingError(AlchemiserError):
    """Raised when logging operations fail."""

    def __init__(self, message: str, logger_name: str | None = None) -> None:
        """Raise when logging infrastructure fails."""
        super().__init__(message)
        self.logger_name = logger_name


class FileOperationError(AlchemiserError):
    """Raised when file operations fail."""

    def __init__(
        self, message: str, file_path: str | None = None, operation: str | None = None
    ) -> None:
        """Raise when a filesystem operation fails."""
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class DatabaseError(AlchemiserError):
    """Raised when database operations fail."""

    def __init__(
        self, message: str, table_name: str | None = None, operation: str | None = None
    ) -> None:
        """Raise when a database operation fails."""
        super().__init__(message)
        self.table_name = table_name
        self.operation = operation


class SecurityError(AlchemiserError):
    """Raised when security-related issues occur."""


class EnvironmentError(ConfigurationError):
    """Raised when environment setup issues occur."""

    def __init__(self, message: str, env_var: str | None = None) -> None:
        """Raise when an environment variable configuration is invalid."""
        super().__init__(message)
        self.env_var = env_var


class StrategyExecutionError(AlchemiserError):
    """Raised when strategy execution fails."""

    def __init__(
        self,
        message: str,
        strategy_name: str | None = None,
        symbol: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Raise when strategy execution encounters an error."""
        context: dict[str, Any] = {}
        if strategy_name:
            context["strategy_name"] = strategy_name
        if symbol:
            context["symbol"] = symbol
        if operation:
            context["operation"] = operation

        super().__init__(message, context)
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.operation = operation


class StrategyValidationError(StrategyExecutionError):
    """Raised when strategy validation fails."""


class EventBusError(AlchemiserError):
    """Raised when event bus operations fail."""

    def __init__(
        self,
        message: str,
        event_type: str | None = None,
        handler_name: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize event bus error with context.

        Args:
            message: Error message
            event_type: Type of event being processed
            handler_name: Name of handler that failed
            correlation_id: Correlation ID for tracing

        """
        context: dict[str, Any] = {}
        if event_type:
            context["event_type"] = event_type
        if handler_name:
            context["handler_name"] = handler_name
        if correlation_id:
            context["correlation_id"] = correlation_id

        super().__init__(message, context)
        self.event_type = event_type
        self.handler_name = handler_name
        self.correlation_id = correlation_id


class HandlerInvocationError(EventBusError):
    """Raised when handler invocation fails."""

    def __init__(
        self,
        message: str,
        event_type: str | None = None,
        handler_name: str | None = None,
        correlation_id: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize handler invocation error with context.

        Args:
            message: Error message
            event_type: Type of event being processed
            handler_name: Name of handler that failed
            correlation_id: Correlation ID for tracing
            original_error: Original exception that caused the failure

        """
        super().__init__(message, event_type, handler_name, correlation_id)
        self.original_error = original_error
        if original_error:
            self.context["original_error"] = str(original_error)
            self.context["original_error_type"] = type(original_error).__name__


class MarketDataServiceError(MarketDataError):
    """Raised when market data service operations fail."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize market data service error with context.

        Args:
            message: Error message
            symbol: Symbol being processed
            operation: Operation that failed
            correlation_id: Correlation ID for tracing

        """
        super().__init__(message, symbol=symbol)
        self.operation = operation
        self.correlation_id = correlation_id
        if operation:
            self.context["operation"] = operation
        if correlation_id:
            self.context["correlation_id"] = correlation_id


class TradingServiceError(TradingClientError):
    """Raised when trading service operations fail."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize trading service error with context.

        Args:
            message: Error message
            symbol: Symbol being processed
            operation: Operation that failed
            correlation_id: Correlation ID for tracing

        """
        super().__init__(message)
        self.symbol = symbol
        self.operation = operation
        self.correlation_id = correlation_id
        if symbol:
            self.context["symbol"] = symbol
        if operation:
            self.context["operation"] = operation
        if correlation_id:
            self.context["correlation_id"] = correlation_id


class PriceValidationError(ValidationError):
    """Raised when price validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        price: float | None = None,
        field_name: str | None = None,
    ) -> None:
        """Initialize price validation error with context.

        Args:
            message: Error message
            symbol: Symbol being validated
            price: Price value that failed validation
            field_name: Name of the price field

        """
        super().__init__(message, field_name=field_name, value=price)
        self.symbol = symbol
        self.price = price
        if symbol:
            self.context["symbol"] = symbol
        if price is not None:
            self.context["price"] = price


class SettlementError(OrderExecutionError):
    """Raised when order settlement monitoring fails."""

    def __init__(
        self,
        message: str,
        order_id: str | None = None,
        symbol: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        """Initialize settlement error with context.

        Args:
            message: Error message
            order_id: Order ID being monitored
            symbol: Symbol being settled
            timeout_seconds: Timeout duration that was exceeded

        """
        super().__init__(message, symbol=symbol, order_id=order_id)
        self.timeout_seconds = timeout_seconds
        if timeout_seconds is not None:
            self.context["timeout_seconds"] = timeout_seconds


class ExecutionManagerError(OrderExecutionError):
    """Raised when execution manager operations fail."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize execution manager error with context.

        Args:
            message: Error message
            operation: Operation that failed
            correlation_id: Correlation ID for tracing

        """
        super().__init__(message)
        self.operation = operation
        self.correlation_id = correlation_id
        if operation:
            self.context["operation"] = operation
        if correlation_id:
            self.context["correlation_id"] = correlation_id


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""

    def __init__(
        self,
        message: str,
        schema_name: str | None = None,
        field_name: str | None = None,
        value: str | int | float | None = None,
    ) -> None:
        """Initialize schema validation error with context.

        Args:
            message: Error message
            schema_name: Name of the schema being validated
            field_name: Name of the field that failed validation
            value: Value that failed validation

        """
        super().__init__(message, field_name=field_name, value=value)
        self.schema_name = schema_name
        if schema_name:
            self.context["schema_name"] = schema_name


class TypeConversionError(AlchemiserError):
    """Raised when type conversion fails."""

    def __init__(
        self,
        message: str,
        source_type: str | None = None,
        target_type: str | None = None,
        value: str | None = None,
    ) -> None:
        """Initialize type conversion error with context.

        Args:
            message: Error message
            source_type: Source type being converted from
            target_type: Target type being converted to
            value: Value that failed conversion

        """
        context: dict[str, Any] = {}
        if source_type:
            context["source_type"] = source_type
        if target_type:
            context["target_type"] = target_type
        if value is not None:
            context["value"] = str(value)

        super().__init__(message, context)
        self.source_type = source_type
        self.target_type = target_type
        self.value = value


class WebSocketConnectionError(WebSocketError):
    """Raised when WebSocket connection issues occur."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """Initialize WebSocket connection error with context.

        Args:
            message: Error message
            url: WebSocket URL that failed
            retry_count: Number of retries attempted

        """
        super().__init__(message)
        self.url = url
        self.retry_count = retry_count
        if url:
            self.context["url"] = url
        if retry_count > 0:
            self.context["retry_count"] = retry_count


class SymbolValidationError(ValidationError):
    """Raised when symbol validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize symbol validation error with context.

        Args:
            message: Error message
            symbol: Symbol that failed validation
            reason: Reason for validation failure

        """
        super().__init__(message, field_name="symbol", value=symbol)
        self.symbol = symbol
        self.reason = reason
        if reason:
            self.context["reason"] = reason


class TimeframeValidationError(ValidationError):
    """Raised when timeframe validation fails."""

    def __init__(
        self,
        message: str,
        timeframe: str | None = None,
        valid_timeframes: list[str] | None = None,
    ) -> None:
        """Initialize timeframe validation error with context.

        Args:
            message: Error message
            timeframe: Timeframe that failed validation
            valid_timeframes: List of valid timeframe options

        """
        super().__init__(message, field_name="timeframe", value=timeframe)
        self.timeframe = timeframe
        self.valid_timeframes = valid_timeframes
        if valid_timeframes:
            self.context["valid_timeframes"] = valid_timeframes


# ═══════════════════════════════════════════════════════════════════════════════
# HEDGE-SPECIFIC EXCEPTIONS (Fail-Closed Safety Rails)
# ═══════════════════════════════════════════════════════════════════════════════


class HedgeFailClosedError(AlchemiserError):
    """Raised when hedge evaluation/execution must fail closed due to safety conditions.

    This exception indicates that hedging cannot proceed due to missing or invalid
    data that would compromise the safety of the hedge. This is a deliberate
    fail-closed behavior - do not retry or fallback to defaults.

    Examples of fail-closed conditions:
    - VIX proxy data unavailable or stale
    - IV/skew data missing or stale
    - Scenario sizing calculation fails
    - Premium cap would be breached
    - All option contracts fail liquidity filters
    - Spread execution unavailable for smoothing template
    """

    def __init__(
        self,
        message: str,
        condition: str | None = None,
        underlying_symbol: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize hedge fail-closed error with context.

        Args:
            message: Human-readable error message
            condition: Specific fail-closed condition that triggered (e.g., "vix_unavailable")
            underlying_symbol: Underlying ETF symbol if applicable
            correlation_id: Correlation ID for tracing

        """
        context: dict[str, Any] = {}
        if condition:
            context["fail_closed_condition"] = condition
        if underlying_symbol:
            context["underlying_symbol"] = underlying_symbol
        if correlation_id:
            context["correlation_id"] = correlation_id

        super().__init__(message, context)
        self.condition = condition
        self.underlying_symbol = underlying_symbol
        self.correlation_id = correlation_id


class VIXProxyUnavailableError(HedgeFailClosedError):
    """Raised when VIX proxy data is unavailable or stale.

    This is a fail-closed condition. Do not default to a VIX tier - the system
    must have real volatility data to make safe hedging decisions.
    """

    def __init__(
        self,
        message: str,
        proxy_symbol: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize VIX proxy unavailable error.

        Args:
            message: Error message
            proxy_symbol: VIX proxy symbol that failed (e.g., "VIXY")
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="vix_proxy_unavailable",
            underlying_symbol=proxy_symbol,
            correlation_id=correlation_id,
        )
        self.proxy_symbol = proxy_symbol


class IVDataStaleError(HedgeFailClosedError):
    """Raised when implied volatility data is stale or unavailable.

    This is a fail-closed condition. Cannot select options safely without
    current IV data.
    """

    def __init__(
        self,
        message: str,
        underlying_symbol: str | None = None,
        data_age_seconds: float | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize IV data stale error.

        Args:
            message: Error message
            underlying_symbol: Underlying symbol
            data_age_seconds: Age of stale data in seconds
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="iv_data_stale",
            underlying_symbol=underlying_symbol,
            correlation_id=correlation_id,
        )
        self.data_age_seconds = data_age_seconds
        if data_age_seconds is not None:
            self.context["data_age_seconds"] = data_age_seconds


class ScenarioSizingFailedError(HedgeFailClosedError):
    """Raised when scenario-based sizing calculation fails.

    This is a fail-closed condition. Cannot size hedges safely without
    valid scenario analysis.
    """

    def __init__(
        self,
        message: str,
        underlying_symbol: str | None = None,
        scenario_move: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize scenario sizing failed error.

        Args:
            message: Error message
            underlying_symbol: Underlying symbol
            scenario_move: Target scenario move (e.g., "-0.20")
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="scenario_sizing_failed",
            underlying_symbol=underlying_symbol,
            correlation_id=correlation_id,
        )
        self.scenario_move = scenario_move
        if scenario_move:
            self.context["scenario_move"] = scenario_move


class PremiumCapBreachedError(HedgeFailClosedError):
    """Raised when hedge premium would exceed maximum allowed percentage of NAV.

    This is a fail-closed condition. Cannot allow oversized hedge positions.
    """

    def __init__(
        self,
        message: str,
        premium_amount: str | None = None,
        premium_cap: str | None = None,
        nav: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize premium cap breached error.

        Args:
            message: Error message
            premium_amount: Attempted premium amount
            premium_cap: Maximum allowed premium
            nav: Portfolio NAV
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="premium_cap_breached",
            correlation_id=correlation_id,
        )
        self.premium_amount = premium_amount
        self.premium_cap = premium_cap
        self.nav = nav
        if premium_amount:
            self.context["premium_amount"] = premium_amount
        if premium_cap:
            self.context["premium_cap"] = premium_cap
        if nav:
            self.context["nav"] = nav


class NoLiquidContractsError(HedgeFailClosedError):
    """Raised when no option contracts pass liquidity filters.

    This is a fail-closed condition. Cannot execute hedges with illiquid options.
    """

    def __init__(
        self,
        message: str,
        underlying_symbol: str | None = None,
        contracts_checked: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize no liquid contracts error.

        Args:
            message: Error message
            underlying_symbol: Underlying symbol
            contracts_checked: Number of contracts that failed filters
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="no_liquid_contracts",
            underlying_symbol=underlying_symbol,
            correlation_id=correlation_id,
        )
        self.contracts_checked = contracts_checked
        if contracts_checked is not None:
            self.context["contracts_checked"] = contracts_checked


class SpreadExecutionUnavailableError(HedgeFailClosedError):
    """Raised when spread execution is unavailable for smoothing template.

    This is a fail-closed condition. Smoothing template requires spread execution;
    do not fallback to single-leg execution.
    """

    def __init__(
        self,
        message: str,
        underlying_symbol: str | None = None,
        long_delta: str | None = None,
        short_delta: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize spread execution unavailable error.

        Args:
            message: Error message
            underlying_symbol: Underlying symbol
            long_delta: Long leg delta
            short_delta: Short leg delta
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="spread_execution_unavailable",
            underlying_symbol=underlying_symbol,
            correlation_id=correlation_id,
        )
        self.long_delta = long_delta
        self.short_delta = short_delta
        if long_delta:
            self.context["long_delta"] = long_delta
        if short_delta:
            self.context["short_delta"] = short_delta


class KillSwitchActiveError(HedgeFailClosedError):
    """Raised when emergency kill switch is active.

    This is a fail-closed condition. System has been manually or automatically
    halted. Do not attempt to execute hedges.
    """

    def __init__(
        self,
        message: str,
        trigger_reason: str | None = None,
        triggered_at: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize kill switch active error.

        Args:
            message: Error message
            trigger_reason: Reason kill switch was triggered
            triggered_at: ISO timestamp when kill switch was activated
            correlation_id: Correlation ID for tracing

        """
        super().__init__(
            message,
            condition="kill_switch_active",
            correlation_id=correlation_id,
        )
        self.trigger_reason = trigger_reason
        self.triggered_at = triggered_at
        if trigger_reason:
            self.context["trigger_reason"] = trigger_reason
        if triggered_at:
            self.context["triggered_at"] = triggered_at
