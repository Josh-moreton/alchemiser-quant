"""Business Unit: shared | Status: current.

Service for generating deterministic account snapshots.

This service orchestrates the collection of data from Alpaca to create complete,
reproducible account snapshots for reporting. Trade ledger data is queried separately
at report generation time using the correlation_id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.account_snapshot_repository import (
    AccountSnapshotRepository,
)
from the_alchemiser.shared.schemas.account_snapshot import (
    AccountSnapshot,
    AlpacaAccountData,
    AlpacaOrderData,
    AlpacaPositionData,
)

if TYPE_CHECKING:
    from alpaca.trading.models import Order, Position, TradeAccount

    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)

__all__ = ["AccountSnapshotService"]


class AccountSnapshotService:
    """Service for generating and storing account snapshots.

    This service collects data from Alpaca API to create deterministic snapshots
    for downstream reporting without live API calls. Trade ledger data is queried
    separately at report generation time using the correlation_id.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        snapshot_repository: AccountSnapshotRepository,
    ) -> None:
        """Initialize snapshot service.

        Args:
            alpaca_manager: Alpaca broker manager for API access
            snapshot_repository: Repository for storing snapshots

        """
        self._alpaca_manager = alpaca_manager
        self._snapshot_repository = snapshot_repository

    def generate_snapshot(
        self,
        account_id: str,
        correlation_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> AccountSnapshot:
        """Generate a complete account snapshot.

        Args:
            account_id: Account identifier
            correlation_id: Workflow correlation ID (used to query trade ledger at report time)
            period_start: Period start timestamp
            period_end: Period end timestamp

        Returns:
            Generated AccountSnapshot

        Raises:
            ValueError: If required data cannot be fetched
            RuntimeError: If snapshot generation fails

        """
        logger.info(
            "Generating account snapshot",
            account_id=account_id,
            correlation_id=correlation_id,
            period_end=period_end.isoformat(),
        )

        try:
            # Fetch Alpaca data
            alpaca_account_data = self._fetch_alpaca_account()
            alpaca_positions_data = self._fetch_alpaca_positions()
            alpaca_orders_data = self._fetch_alpaca_orders()

            # Create snapshot
            snapshot_id = str(uuid4())
            created_at = datetime.now(UTC)

            # Build snapshot data for checksum
            snapshot_dict = {
                "snapshot_id": snapshot_id,
                "snapshot_version": "1.0",
                "account_id": account_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "correlation_id": correlation_id,
                "created_at": created_at.isoformat(),
                "alpaca_account": alpaca_account_data.model_dump(),
                "alpaca_positions": [pos.model_dump() for pos in alpaca_positions_data],
                "alpaca_orders": [order.model_dump() for order in alpaca_orders_data],
            }

            # Calculate checksum
            checksum = AccountSnapshot.calculate_checksum(snapshot_dict)

            # Create AccountSnapshot instance
            snapshot = AccountSnapshot(
                snapshot_id=snapshot_id,
                snapshot_version="1.0",
                account_id=account_id,
                period_start=period_start,
                period_end=period_end,
                correlation_id=correlation_id,
                created_at=created_at,
                alpaca_account=alpaca_account_data,
                alpaca_positions=alpaca_positions_data,
                alpaca_orders=alpaca_orders_data,
                checksum=checksum,
            )

            # Verify checksum
            if not snapshot.verify_checksum():
                raise RuntimeError("Snapshot checksum verification failed")

            # Store snapshot
            self._snapshot_repository.put_snapshot(snapshot)

            logger.info(
                "Account snapshot generated successfully",
                snapshot_id=snapshot_id,
                account_id=account_id,
                correlation_id=correlation_id,
            )

            return snapshot

        except Exception as e:
            logger.error(
                "Failed to generate account snapshot",
                account_id=account_id,
                correlation_id=correlation_id,
                error=str(e),
            )
            raise

    def _fetch_alpaca_account(self) -> AlpacaAccountData:
        """Fetch and convert Alpaca account data.

        Returns:
            AlpacaAccountData DTO

        Raises:
            ValueError: If account data cannot be fetched

        """
        account_obj = self._alpaca_manager.get_account_object()
        if not account_obj:
            raise ValueError("Failed to fetch Alpaca account data")

        return self._convert_account_to_dto(account_obj)

    def _convert_account_to_dto(self, account: TradeAccount) -> AlpacaAccountData:
        """Convert Alpaca TradeAccount to DTO.

        Args:
            account: Alpaca TradeAccount object

        Returns:
            AlpacaAccountData DTO

        """
        return AlpacaAccountData(
            account_id=str(account.id),
            account_number=str(account.account_number) if account.account_number else None,
            status=str(account.status),
            currency=str(account.currency) if account.currency else "USD",
            buying_power=Decimal(str(account.buying_power)),
            cash=Decimal(str(account.cash)),
            equity=Decimal(str(account.equity)),
            portfolio_value=Decimal(str(account.portfolio_value)),
            last_equity=Decimal(str(account.last_equity)) if account.last_equity else None,
            long_market_value=(
                Decimal(str(account.long_market_value)) if account.long_market_value else None
            ),
            short_market_value=(
                Decimal(str(account.short_market_value)) if account.short_market_value else None
            ),
            initial_margin=Decimal(str(account.initial_margin)) if account.initial_margin else None,
            maintenance_margin=(
                Decimal(str(account.maintenance_margin)) if account.maintenance_margin else None
            ),
        )

    def _fetch_alpaca_positions(self) -> list[AlpacaPositionData]:
        """Fetch and convert Alpaca positions.

        Returns:
            List of AlpacaPositionData DTOs

        """
        positions = self._alpaca_manager.get_positions()
        return [self._convert_position_to_dto(pos) for pos in positions]

    def _convert_position_to_dto(self, position: Position) -> AlpacaPositionData:
        """Convert Alpaca Position to DTO.

        Args:
            position: Alpaca Position object

        Returns:
            AlpacaPositionData DTO

        """
        return AlpacaPositionData(
            symbol=str(position.symbol),
            qty=Decimal(str(position.qty)),
            qty_available=(
                Decimal(str(position.qty_available)) if position.qty_available else None
            ),
            avg_entry_price=Decimal(str(position.avg_entry_price)),
            current_price=Decimal(str(position.current_price)),
            market_value=Decimal(str(position.market_value)),
            cost_basis=Decimal(str(position.cost_basis)),
            unrealized_pl=Decimal(str(position.unrealized_pl)),
            unrealized_plpc=Decimal(str(position.unrealized_plpc)),
            unrealized_intraday_pl=(
                Decimal(str(position.unrealized_intraday_pl))
                if position.unrealized_intraday_pl
                else None
            ),
            unrealized_intraday_plpc=(
                Decimal(str(position.unrealized_intraday_plpc))
                if position.unrealized_intraday_plpc
                else None
            ),
            side=str(position.side),
            asset_class=str(position.asset_class) if position.asset_class else "us_equity",
        )

    def _fetch_alpaca_orders(self) -> list[AlpacaOrderData]:
        """Fetch and convert Alpaca orders.

        Returns:
            List of AlpacaOrderData DTOs

        """
        # Fetch recent filled orders (we can extend this to include all statuses if needed)
        orders = self._alpaca_manager.get_orders(status="closed")
        return [self._convert_order_to_dto(order) for order in orders]

    def _convert_order_to_dto(self, order: Order) -> AlpacaOrderData:
        """Convert Alpaca Order to DTO.

        Args:
            order: Alpaca Order object

        Returns:
            AlpacaOrderData DTO

        """
        return AlpacaOrderData(
            order_id=str(order.id),
            symbol=str(order.symbol),
            side=str(order.side),
            order_type=str(order.order_type),
            qty=Decimal(str(order.qty)) if order.qty else None,
            notional=Decimal(str(order.notional)) if order.notional else None,
            filled_qty=Decimal(str(order.filled_qty)) if order.filled_qty else Decimal("0"),
            filled_avg_price=(
                Decimal(str(order.filled_avg_price)) if order.filled_avg_price else None
            ),
            status=str(order.status),
            time_in_force=str(order.time_in_force),
            limit_price=Decimal(str(order.limit_price)) if order.limit_price else None,
            stop_price=Decimal(str(order.stop_price)) if order.stop_price else None,
            submitted_at=order.submitted_at,
            filled_at=order.filled_at,
            expired_at=order.expired_at,
            canceled_at=order.canceled_at,
        )
