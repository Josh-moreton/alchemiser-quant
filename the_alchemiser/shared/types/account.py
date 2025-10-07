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
    """

    account_id: str
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    day_trades_remaining: int
    portfolio_value: Decimal
    last_equity: Decimal
    daytrading_buying_power: Decimal
    regt_buying_power: Decimal
    status: Literal["ACTIVE", "INACTIVE"]

    @classmethod
    def from_dict(cls, data: AccountInfo) -> AccountModel:
        """Create from AccountInfo TypedDict.

        Stores Decimal values directly without conversion.
        """
        return cls(
            account_id=data["account_id"],
            equity=data["equity"],
            cash=data["cash"],
            buying_power=data["buying_power"],
            day_trades_remaining=data["day_trades_remaining"],
            portfolio_value=data["portfolio_value"],
            last_equity=data["last_equity"],
            daytrading_buying_power=data["daytrading_buying_power"],
            regt_buying_power=data["regt_buying_power"],
            status=data["status"],
        )

    def to_dict(self) -> AccountInfo:
        """Convert to AccountInfo TypedDict.

        Returns Decimal values directly without conversion.
        """
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
