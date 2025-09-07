"""Business Unit: execution | Status: current.

Account management service handling account operations, risk metrics, and buying power.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from the_alchemiser.execution.brokers.account_service import AccountService
from the_alchemiser.execution.mappers.core_execution_mappers import (
    account_summary_to_typed,
    account_typed_to_serializable,
)
from the_alchemiser.execution.mappers.service_dto_mappers import (
    account_summary_typed_to_dto,
    dict_to_buying_power_dto,
    dict_to_enriched_account_summary_dto,
    dict_to_portfolio_allocation_dto,
    dict_to_risk_metrics_dto,
    dict_to_trade_eligibility_dto,
)
from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.shared.schemas.accounts import (
    AccountMetricsDTO,
    AccountSummaryDTO,
    BuyingPowerDTO,
    EnrichedAccountSummaryDTO,
    PortfolioAllocationDTO,
    RiskMetricsDTO,
    TradeEligibilityDTO,
)
from the_alchemiser.shared.utils.decorators import translate_trading_errors


class AccountManagementService:
    """Service responsible for account management operations.

    Handles account summaries, risk metrics, buying power, and trade eligibility.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize the account management service.

        Args:
            alpaca_manager: The Alpaca manager for broker operations

        """
        self.logger = logging.getLogger(__name__)
        self.alpaca_manager = alpaca_manager
        self.account = AccountService(alpaca_manager)

    def get_account_summary(self) -> AccountSummaryDTO:
        """Get comprehensive account summary with metrics."""
        account_dict = self.account.get_account_summary()
        # Convert to typed and then to DTO
        typed = account_summary_to_typed(account_dict)
        return account_summary_typed_to_dto(typed)

    def check_buying_power(self, required_amount: float) -> BuyingPowerDTO:
        """Check available buying power."""
        buying_power_dict = self.account.check_buying_power(required_amount)
        return dict_to_buying_power_dto(buying_power_dict)

    def get_risk_metrics(self) -> RiskMetricsDTO:
        """Calculate comprehensive risk metrics."""
        risk_metrics_dict = self.account.get_risk_metrics()
        return dict_to_risk_metrics_dto(risk_metrics_dict)

    def validate_trade_eligibility(
        self, symbol: str, quantity: int, side: str, estimated_cost: float | None = None
    ) -> TradeEligibilityDTO:
        """Validate if a trade can be executed."""
        eligibility_dict = self.account.validate_trade_eligibility(
            symbol, quantity, side, estimated_cost or 0.0
        )
        return dict_to_trade_eligibility_dto(eligibility_dict)

    def get_portfolio_allocation(self) -> PortfolioAllocationDTO:
        """Get portfolio allocation and diversification metrics."""
        allocation_dict = self.account.get_portfolio_allocation()
        return dict_to_portfolio_allocation_dto(allocation_dict)

    @translate_trading_errors(
        default_return=EnrichedAccountSummaryDTO(
            raw={},
            summary=AccountSummaryDTO(
                account_id="error",
                equity=Decimal("0"),
                cash=Decimal("0"),
                market_value=Decimal("0"),
                buying_power=Decimal("0"),
                last_equity=Decimal("0"),
                day_trade_count=0,
                pattern_day_trader=False,
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                calculated_metrics=AccountMetricsDTO(
                    cash_ratio=Decimal("0"),
                    market_exposure=Decimal("0"),
                    leverage_ratio=None,
                    available_buying_power_ratio=Decimal("0"),
                ),
            ),
        )
    )
    def get_account_summary_enriched(self) -> EnrichedAccountSummaryDTO:
        """Enriched account summary with typed domain objects.

        Returns structured data including both the raw provider dictionary and typed domain
        objects. The raw dict is preserved for backward-compatible display layers; the typed
        structure should be preferred for all business logic.
        """
        legacy = self.account.get_account_summary()

        # Always return typed path (using typed domain)
        typed = account_summary_to_typed(legacy)
        enriched_dict = {"raw": legacy, "summary": account_typed_to_serializable(typed)}
        return dict_to_enriched_account_summary_dto(enriched_dict)
