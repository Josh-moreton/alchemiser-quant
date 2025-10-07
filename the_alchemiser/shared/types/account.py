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
    """Immutable account information model."""

    account_id: str
    equity: float
    cash: float
    buying_power: float
    day_trades_remaining: int
    portfolio_value: float
    last_equity: float
    daytrading_buying_power: float
    regt_buying_power: float
    status: Literal["ACTIVE", "INACTIVE"]

    @classmethod
    def from_dict(cls, data: AccountInfo) -> AccountModel:
        """Create from AccountInfo TypedDict.

        Converts Decimal values from TypedDict to float for internal storage.
        """
        return cls(
            account_id=data["account_id"],
            equity=float(data["equity"]),
            cash=float(data["cash"]),
            buying_power=float(data["buying_power"]),
            day_trades_remaining=data["day_trades_remaining"],
            portfolio_value=float(data["portfolio_value"]),
            last_equity=float(data["last_equity"]),
            daytrading_buying_power=float(data["daytrading_buying_power"]),
            regt_buying_power=float(data["regt_buying_power"]),
            status=data["status"],
        )

    def to_dict(self) -> AccountInfo:
        """Convert to AccountInfo TypedDict.

        Converts float values to Decimal for TypedDict compliance.
        """
        return {
            "account_id": self.account_id,
            "equity": Decimal(str(self.equity)),
            "cash": Decimal(str(self.cash)),
            "buying_power": Decimal(str(self.buying_power)),
            "day_trades_remaining": self.day_trades_remaining,
            "portfolio_value": Decimal(str(self.portfolio_value)),
            "last_equity": Decimal(str(self.last_equity)),
            "daytrading_buying_power": Decimal(str(self.daytrading_buying_power)),
            "regt_buying_power": Decimal(str(self.regt_buying_power)),
            "status": self.status,
        }


@dataclass(frozen=True)
class PortfolioHistoryModel:
    """Immutable portfolio history model."""

    profit_loss: list[float]
    profit_loss_pct: list[float]
    equity: list[float]
    timestamp: list[str]

    @classmethod
    def from_dict(cls, data: PortfolioHistoryData) -> PortfolioHistoryModel:
        """Create from PortfolioHistoryData TypedDict.

        Converts Decimal values from TypedDict to float for internal storage.
        """
        return cls(
            profit_loss=[float(x) for x in data.get("profit_loss", [])],
            profit_loss_pct=[float(x) for x in data.get("profit_loss_pct", [])],
            equity=[float(x) for x in data.get("equity", [])],
            timestamp=data.get("timestamp", []),
        )

    def to_dict(self) -> PortfolioHistoryData:
        """Convert to PortfolioHistoryData TypedDict.

        Converts float values to Decimal for TypedDict compliance.
        """
        return {
            "profit_loss": [Decimal(str(x)) for x in self.profit_loss],
            "profit_loss_pct": [Decimal(str(x)) for x in self.profit_loss_pct],
            "equity": [Decimal(str(x)) for x in self.equity],
            "timestamp": self.timestamp,
        }

    @property
    def is_empty(self) -> bool:
        """Check if portfolio history is empty."""
        return not any([self.profit_loss, self.equity, self.timestamp])

    @property
    def latest_equity(self) -> float | None:
        """Get the latest equity value."""
        return self.equity[-1] if self.equity else None

    @property
    def latest_pnl(self) -> float | None:
        """Get the latest P&L value."""
        return self.profit_loss[-1] if self.profit_loss else None
