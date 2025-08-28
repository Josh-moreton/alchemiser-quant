"""Business Unit: utilities; Status: current.

Account domain models.
"""
from __future__ import annotations


from dataclasses import dataclass
from typing import Literal

from the_alchemiser.domain.types import AccountInfo, PortfolioHistoryData


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
        """Create from AccountInfo TypedDict."""
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
        """Convert to AccountInfo TypedDict."""
        return {
            "account_id": self.account_id,
            "equity": self.equity,
            "cash": self.cash,
            "buying_power": self.buying_power,
            "day_trades_remaining": self.day_trades_remaining,
            "portfolio_value": self.portfolio_value,
            "last_equity": self.last_equity,
            "daytrading_buying_power": self.daytrading_buying_power,
            "regt_buying_power": self.regt_buying_power,
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
        """Create from PortfolioHistoryData TypedDict."""
        return cls(
            profit_loss=data.get("profit_loss", []),
            profit_loss_pct=data.get("profit_loss_pct", []),
            equity=data.get("equity", []),
            timestamp=data.get("timestamp", []),
        )

    def to_dict(self) -> PortfolioHistoryData:
        """Convert to PortfolioHistoryData TypedDict."""
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
    def latest_equity(self) -> float | None:
        """Get the latest equity value."""
        return self.equity[-1] if self.equity else None

    @property
    def latest_pnl(self) -> float | None:
        """Get the latest P&L value."""
        return self.profit_loss[-1] if self.profit_loss else None
