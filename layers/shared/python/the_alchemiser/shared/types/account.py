"""Business Unit: utilities; Status: current.

Account domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from the_alchemiser.shared.value_objects.core_types import AccountInfo, PortfolioHistoryData


@dataclass(frozen=True)
class AccountModel:
    """Immutable account information model.

    All monetary values use Decimal for precision per guardrails.
    Includes all fields from Alpaca GET /v2/account endpoint.
    """

    # Identity
    account_id: str
    status: Literal["ACTIVE", "INACTIVE"]

    # Core financial values
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    portfolio_value: Decimal
    last_equity: Decimal
    long_market_value: Decimal | None = None
    short_market_value: Decimal | None = None

    # Margin fields
    initial_margin: Decimal | None = None
    maintenance_margin: Decimal | None = None
    last_maintenance_margin: Decimal | None = None
    sma: Decimal | None = None  # Special Memorandum Account

    # Buying power variants
    regt_buying_power: Decimal | None = None  # Reg T overnight
    daytrading_buying_power: Decimal | None = None  # PDT 4x intraday
    multiplier: int | None = None  # 1=cash, 2=margin, 4=PDT

    # Day trading status
    daytrade_count: int | None = None
    pattern_day_trader: bool | None = None

    # Account status flags
    trading_blocked: bool | None = None
    transfers_blocked: bool | None = None
    account_blocked: bool | None = None
    shorting_enabled: bool | None = None

    @classmethod
    def from_dict(cls, data: AccountInfo) -> AccountModel:
        """Create from AccountInfo TypedDict.

        Stores Decimal values directly without conversion.
        Handles optional fields gracefully.
        """
        return cls(
            account_id=data.get("account_id", ""),
            status=data.get("status", "INACTIVE"),
            equity=data.get("equity", Decimal("0")),
            cash=data.get("cash", Decimal("0")),
            buying_power=data.get("buying_power", Decimal("0")),
            portfolio_value=data.get("portfolio_value", Decimal("0")),
            last_equity=data.get("last_equity", Decimal("0")),
            long_market_value=data.get("long_market_value"),
            short_market_value=data.get("short_market_value"),
            initial_margin=data.get("initial_margin"),
            maintenance_margin=data.get("maintenance_margin"),
            last_maintenance_margin=data.get("last_maintenance_margin"),
            sma=data.get("sma"),
            regt_buying_power=data.get("regt_buying_power"),
            daytrading_buying_power=data.get("daytrading_buying_power"),
            multiplier=data.get("multiplier"),
            daytrade_count=data.get("daytrade_count"),
            pattern_day_trader=data.get("pattern_day_trader"),
            trading_blocked=data.get("trading_blocked"),
            transfers_blocked=data.get("transfers_blocked"),
            account_blocked=data.get("account_blocked"),
            shorting_enabled=data.get("shorting_enabled"),
        )

    def to_dict(self) -> AccountInfo:
        """Convert to AccountInfo TypedDict.

        Returns Decimal values directly without conversion.
        Only includes fields that are set (not None).
        """
        result: AccountInfo = {
            "account_id": self.account_id,
            "status": self.status,
            "equity": self.equity,
            "cash": self.cash,
            "buying_power": self.buying_power,
            "portfolio_value": self.portfolio_value,
            "last_equity": self.last_equity,
        }
        # Add optional fields if set (grouped to reduce complexity)
        self._add_optional_market_values(result)
        self._add_optional_margin_fields(result)
        self._add_optional_buying_power_fields(result)
        self._add_optional_status_fields(result)
        return result

    def _add_optional_market_values(self, result: AccountInfo) -> None:
        """Add optional market value fields to result dict."""
        if self.long_market_value is not None:
            result["long_market_value"] = self.long_market_value
        if self.short_market_value is not None:
            result["short_market_value"] = self.short_market_value

    def _add_optional_margin_fields(self, result: AccountInfo) -> None:
        """Add optional margin fields to result dict."""
        if self.initial_margin is not None:
            result["initial_margin"] = self.initial_margin
        if self.maintenance_margin is not None:
            result["maintenance_margin"] = self.maintenance_margin
        if self.last_maintenance_margin is not None:
            result["last_maintenance_margin"] = self.last_maintenance_margin
        if self.sma is not None:
            result["sma"] = self.sma

    def _add_optional_buying_power_fields(self, result: AccountInfo) -> None:
        """Add optional buying power and day trading fields to result dict."""
        if self.regt_buying_power is not None:
            result["regt_buying_power"] = self.regt_buying_power
        if self.daytrading_buying_power is not None:
            result["daytrading_buying_power"] = self.daytrading_buying_power
        if self.multiplier is not None:
            result["multiplier"] = self.multiplier
        if self.daytrade_count is not None:
            result["daytrade_count"] = self.daytrade_count
        if self.pattern_day_trader is not None:
            result["pattern_day_trader"] = self.pattern_day_trader

    def _add_optional_status_fields(self, result: AccountInfo) -> None:
        """Add optional account status fields to result dict."""
        if self.trading_blocked is not None:
            result["trading_blocked"] = self.trading_blocked
        if self.transfers_blocked is not None:
            result["transfers_blocked"] = self.transfers_blocked
        if self.account_blocked is not None:
            result["account_blocked"] = self.account_blocked
        if self.shorting_enabled is not None:
            result["shorting_enabled"] = self.shorting_enabled


@dataclass(frozen=True)
class PortfolioHistoryModel:
    """Immutable portfolio history model.

    All monetary values use Decimal for precision per guardrails.
    """

    profit_loss: list[Decimal]
    profit_loss_pct: list[Decimal]
    equity: list[Decimal]
    timestamp: list[str]

    @classmethod
    def from_dict(cls, data: PortfolioHistoryData) -> PortfolioHistoryModel:
        """Create from PortfolioHistoryData TypedDict.

        Stores Decimal values directly without conversion.
        """
        return cls(
            profit_loss=list(data.get("profit_loss", [])),
            profit_loss_pct=list(data.get("profit_loss_pct", [])),
            equity=list(data.get("equity", [])),
            timestamp=data.get("timestamp", []),
        )

    def to_dict(self) -> PortfolioHistoryData:
        """Convert to PortfolioHistoryData TypedDict.

        Returns Decimal values directly without conversion.
        """
        return {
            "profit_loss": self.profit_loss,
            "profit_loss_pct": self.profit_loss_pct,
            "equity": self.equity,
            "timestamp": self.timestamp,
        }

    @property
    def is_empty(self) -> bool:
        """Check if portfolio history is empty."""
        return not any([self.profit_loss, self.equity, self.timestamp])

    @property
    def latest_equity(self) -> Decimal | None:
        """Get the latest equity value."""
        return self.equity[-1] if self.equity else None

    @property
    def latest_pnl(self) -> Decimal | None:
        """Get the latest P&L value."""
        return self.profit_loss[-1] if self.profit_loss else None
