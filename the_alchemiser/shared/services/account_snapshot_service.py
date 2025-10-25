"""Business Unit: shared | Status: current.

Account snapshot service for deterministic reporting.

This service aggregates data from Alpaca API and internal ledger to create
complete, versioned account snapshots. Snapshots are persisted to S3 for
downstream consumption by reporting services.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.account_snapshot import (
    AccountSnapshot,
    AlpacaAccountData,
    AlpacaOrderData,
    AlpacaPositionData,
    InternalLedgerData,
    StrategyPerformance,
)

if TYPE_CHECKING:
    from alpaca.trading.models import Order, Position, TradeAccount

    from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService
    from the_alchemiser.shared.schemas.trade_ledger import TradeLedger
    from the_alchemiser.shared.services.alpaca_account_service import (
        AlpacaAccountService,
    )

logger = get_logger(__name__)

__all__ = ["AccountSnapshotService"]


class S3ClientProtocol(Protocol):
    """Protocol for boto3 S3 client interface (subset used)."""

    def put_object(
        self,
        Bucket: str,
        Key: str,
        Body: str,
        ContentType: str,
        ServerSideEncryption: str,
        Metadata: dict[str, str],
    ) -> dict[str, Any]: ...


class AccountSnapshotService:
    """Service for generating and persisting account snapshots.

    Aggregates data from Alpaca API and internal ledger to create
    complete account state snapshots for deterministic reporting.
    """

    def __init__(
        self,
        alpaca_account_service: AlpacaAccountService,
        trade_ledger_service: TradeLedgerService,
    ) -> None:
        """Initialize snapshot service with required dependencies.

        Args:
            alpaca_account_service: Service for Alpaca account operations
            trade_ledger_service: Service for internal trade ledger

        """
        self._alpaca_service = alpaca_account_service
        self._ledger_service = trade_ledger_service
        self._settings = load_settings()
        self._s3_client: S3ClientProtocol | None = None
        self._s3_init_failed: bool = False

    def _init_s3_client(self) -> S3ClientProtocol | None:
        """Initialize boto3 S3 client lazily.

        Returns:
            boto3 S3 client instance or None if initialization failed

        """
        if self._s3_init_failed:
            return None

        if self._s3_client is not None:
            return self._s3_client

        try:
            import boto3

            self._s3_client = boto3.client("s3")
            return self._s3_client
        except ImportError:
            logger.warning("boto3 not available, S3 snapshot persistence disabled")
            self._s3_init_failed = True
            return None
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {e}")
            self._s3_init_failed = True
            return None

    def _convert_alpaca_account(
        self,
        account: TradeAccount,
        captured_at: datetime,
    ) -> AlpacaAccountData:
        """Convert Alpaca TradeAccount to our DTO.

        Args:
            account: Alpaca TradeAccount object
            captured_at: When the data was captured

        Returns:
            AlpacaAccountData DTO

        """
        # Handle unrealized_pl - may not be available on all account types
        unrealized_pl = None
        if hasattr(account, "unrealized_pl") and account.unrealized_pl is not None:
            unrealized_pl = Decimal(str(account.unrealized_pl))

        return AlpacaAccountData(
            account_id=str(account.id),
            account_number=str(account.account_number),
            status=str(
                account.status.value if hasattr(account.status, "value") else account.status
            ),
            currency=str(account.currency) if account.currency else "USD",
            buying_power=Decimal(str(account.buying_power)),
            cash=Decimal(str(account.cash)),
            equity=Decimal(str(account.equity)),
            portfolio_value=Decimal(str(account.portfolio_value)),
            unrealized_pl=unrealized_pl,
            realized_pl=None,  # Not typically available from TradeAccount
            initial_margin=Decimal(str(account.initial_margin))
            if hasattr(account, "initial_margin") and account.initial_margin is not None
            else None,
            maintenance_margin=Decimal(str(account.maintenance_margin))
            if hasattr(account, "maintenance_margin") and account.maintenance_margin is not None
            else None,
            last_equity=Decimal(str(account.last_equity))
            if hasattr(account, "last_equity") and account.last_equity is not None
            else None,
            captured_at=captured_at,
        )

    def _convert_alpaca_position(self, position: Position) -> AlpacaPositionData:
        """Convert Alpaca Position to our DTO.

        Args:
            position: Alpaca Position object

        Returns:
            AlpacaPositionData DTO

        """
        return AlpacaPositionData(
            symbol=str(position.symbol),
            qty=Decimal(str(position.qty)),
            market_value=Decimal(str(position.market_value)),
            avg_entry_price=Decimal(str(position.avg_entry_price)),
            current_price=Decimal(str(position.current_price)),
            unrealized_pl=Decimal(str(position.unrealized_pl)),
            unrealized_plpc=Decimal(str(position.unrealized_plpc)),
            cost_basis=Decimal(str(position.cost_basis)),
            asset_id=str(position.asset_id)
            if hasattr(position, "asset_id") and position.asset_id
            else None,
            exchange=str(position.exchange)
            if hasattr(position, "exchange") and position.exchange
            else None,
        )

    def _convert_alpaca_order(self, order: Order) -> AlpacaOrderData:
        """Convert Alpaca Order to our DTO.

        Args:
            order: Alpaca Order object

        Returns:
            AlpacaOrderData DTO

        """
        # Extract side - handle both enum and string formats
        side_value = str(
            order.side.value if hasattr(order.side, "value") and order.side else order.side
        ).lower()
        # Validate it's either buy or sell
        if side_value not in ("buy", "sell"):
            side_value = "buy"  # Default to buy if invalid

        return AlpacaOrderData(
            order_id=str(order.id),
            symbol=str(order.symbol),
            side=side_value,  # type: ignore[arg-type]  # We validated above
            order_type=str(
                order.type.value if hasattr(order.type, "value") and order.type else order.type
            ),
            status=str(
                order.status.value
                if hasattr(order.status, "value") and order.status
                else order.status
            ),
            qty=Decimal(str(order.qty)),
            filled_qty=Decimal(str(order.filled_qty)) if order.filled_qty else Decimal("0"),
            limit_price=Decimal(str(order.limit_price)) if order.limit_price else None,
            filled_avg_price=Decimal(str(order.filled_avg_price))
            if order.filled_avg_price
            else None,
            submitted_at=order.submitted_at,
            filled_at=order.filled_at if hasattr(order, "filled_at") else None,
            commission=None,  # Not typically available from Order object
        )

    def _build_ledger_data(self) -> InternalLedgerData:
        """Build internal ledger data from trade ledger service.

        Returns:
            InternalLedgerData DTO

        """
        ledger = self._ledger_service.get_ledger()

        # Get recent trades (limit to last 100 for snapshot size)
        recent_trades = []
        for entry in ledger.entries[-100:]:
            recent_trades.append(entry.model_dump(mode="json"))

        # Extract unique strategies
        strategies_active = []
        for entry in ledger.entries:
            for strategy in entry.strategy_names:
                if strategy and strategy not in strategies_active:
                    strategies_active.append(strategy)

        # Compute per-strategy performance metrics
        strategy_performance = self._compute_strategy_performance(ledger)

        # Note: strategy allocations would come from configuration or metadata
        # For now, we'll leave it empty or extract from available data
        strategy_allocations: dict[str, Decimal] = {}

        return InternalLedgerData(
            ledger_id=ledger.ledger_id,
            total_trades=ledger.total_entries,
            total_buy_value=ledger.total_buy_value,
            total_sell_value=ledger.total_sell_value,
            strategies_active=strategies_active,
            strategy_allocations=strategy_allocations,
            strategy_performance=strategy_performance,
            recent_trades=recent_trades,
        )

    def _compute_strategy_performance(
        self, ledger: TradeLedger
    ) -> dict[str, StrategyPerformance]:
        """Compute per-strategy performance metrics from trade ledger.

        Args:
            ledger: Trade ledger with entries

        Returns:
            Dictionary mapping strategy name to performance metrics

        """
        from collections import defaultdict

        # Track metrics per strategy
        strategy_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "total_buy_value": Decimal("0"),
                "total_sell_value": Decimal("0"),
                "symbols": set(),
                "first_trade_at": None,
                "last_trade_at": None,
            }
        )

        # Process each trade entry
        for entry in ledger.entries:
            # Handle multi-strategy attribution
            if entry.strategy_names:
                # Use strategy weights if available, otherwise equal distribution
                if entry.strategy_weights:
                    weights = entry.strategy_weights
                else:
                    # Equal weight distribution if no weights specified
                    num_strategies = len(entry.strategy_names)
                    weights = {
                        name: Decimal("1") / Decimal(str(num_strategies))
                        for name in entry.strategy_names
                    }

                # Allocate metrics to each strategy based on weights
                for strategy_name in entry.strategy_names:
                    weight = weights.get(strategy_name, Decimal("0"))
                    if weight == 0:
                        continue

                    data = strategy_data[strategy_name]
                    data["total_trades"] += 1

                    trade_value = entry.filled_qty * entry.fill_price

                    if entry.direction == "BUY":
                        data["buy_trades"] += 1
                        data["total_buy_value"] += trade_value * weight
                    else:  # SELL
                        data["sell_trades"] += 1
                        data["total_sell_value"] += trade_value * weight

                    data["symbols"].add(entry.symbol)

                    # Track timing
                    if (
                        data["first_trade_at"] is None
                        or entry.fill_timestamp < data["first_trade_at"]
                    ):
                        data["first_trade_at"] = entry.fill_timestamp
                    if (
                        data["last_trade_at"] is None
                        or entry.fill_timestamp > data["last_trade_at"]
                    ):
                        data["last_trade_at"] = entry.fill_timestamp

        # Build StrategyPerformance DTOs
        performance_map = {}
        for strategy_name, data in strategy_data.items():
            # Compute P&L metrics
            gross_pnl = data["total_sell_value"] - data["total_buy_value"]

            # Realized P&L is the same as gross P&L for completed trades
            # (more sophisticated P&L calculation would require position tracking)
            realized_pnl = gross_pnl

            performance_map[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=data["total_trades"],
                buy_trades=data["buy_trades"],
                sell_trades=data["sell_trades"],
                total_buy_value=data["total_buy_value"],
                total_sell_value=data["total_sell_value"],
                realized_pnl=realized_pnl,
                gross_pnl=gross_pnl,
                symbols_traded=sorted(data["symbols"]),
                allocation_weight=None,  # Would need to come from config
                first_trade_at=data["first_trade_at"],
                last_trade_at=data["last_trade_at"],
            )

        return performance_map

    def generate_snapshot(
        self,
        correlation_id: str,
        period_start: datetime,
        period_end: datetime | None = None,
    ) -> AccountSnapshot:
        """Generate a complete account snapshot.

        Args:
            correlation_id: Workflow correlation ID
            period_start: Start of trading period
            period_end: End of trading period (defaults to now)

        Returns:
            AccountSnapshot with all aggregated data

        Raises:
            Exception: If critical data cannot be retrieved

        """
        logger.info(
            "Generating account snapshot",
            correlation_id=correlation_id,
            period_start=period_start.isoformat(),
        )

        # Default period_end to now if not provided
        if period_end is None:
            period_end = datetime.now(UTC)

        captured_at = datetime.now(UTC)

        # Fetch Alpaca account data
        account_obj = self._alpaca_service.get_account_object()
        if not account_obj:
            raise ValueError("Failed to retrieve Alpaca account data for snapshot")

        alpaca_account = self._convert_alpaca_account(account_obj, captured_at)

        # Fetch positions
        alpaca_positions = []
        try:
            positions = self._alpaca_service.get_all_positions()
            if positions:
                alpaca_positions = [self._convert_alpaca_position(pos) for pos in positions]
        except Exception as e:
            logger.warning(f"Failed to fetch positions for snapshot: {e}")

        # Fetch recent orders (last 100)
        alpaca_orders = []
        try:
            # Import here to avoid circular dependency
            from alpaca.trading.enums import QueryOrderStatus
            from alpaca.trading.requests import GetOrdersRequest

            trading_client = self._alpaca_service._trading_client
            request = GetOrdersRequest(
                status=QueryOrderStatus.ALL,
                limit=100,
            )
            orders = trading_client.get_orders(request)
            if orders:
                # Filter out any non-Order objects (should not happen but safety check)
                from alpaca.trading.models import Order as AlpacaOrder

                alpaca_orders = [
                    self._convert_alpaca_order(order)
                    for order in orders
                    if isinstance(order, AlpacaOrder)
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch orders for snapshot: {e}")

        # Build internal ledger data
        internal_ledger = self._build_ledger_data()

        # Create snapshot
        snapshot_id = str(uuid.uuid4())
        snapshot = AccountSnapshot(
            snapshot_version="1.0",
            snapshot_id=snapshot_id,
            account_id=alpaca_account.account_id,
            period_start=period_start,
            period_end=period_end,
            created_at=captured_at,
            correlation_id=correlation_id,
            alpaca_account=alpaca_account,
            alpaca_positions=alpaca_positions,
            alpaca_orders=alpaca_orders,
            internal_ledger=internal_ledger,
            metadata={
                "total_positions": len(alpaca_positions),
                "total_orders": len(alpaca_orders),
                "snapshot_generation_success": True,
            },
        )

        # Compute and add checksum
        checksum = snapshot.compute_checksum()

        # Create new snapshot with checksum (frozen model requires reconstruction)
        snapshot_with_checksum = AccountSnapshot(
            **snapshot.model_dump(exclude={"checksum"}),
            checksum=checksum,
        )

        logger.info(
            "Account snapshot generated successfully",
            snapshot_id=snapshot_id,
            correlation_id=correlation_id,
            total_positions=len(alpaca_positions),
            total_orders=len(alpaca_orders),
            total_ledger_trades=internal_ledger.total_trades,
        )

        return snapshot_with_checksum

    def persist_to_s3(self, snapshot: AccountSnapshot, bucket_name: str) -> str | None:
        """Persist snapshot to S3 with deterministic pathing.

        Args:
            snapshot: Account snapshot to persist
            bucket_name: S3 bucket name

        Returns:
            S3 URI of persisted snapshot, or None if failed

        """
        if not bucket_name:
            logger.warning("S3 bucket name not configured, skipping snapshot persistence")
            return None

        s3_client = self._init_s3_client()
        if not s3_client:
            logger.warning("S3 client not available, skipping snapshot persistence")
            return None

        try:
            # Generate deterministic S3 key
            s3_key = snapshot.s3_key

            # Serialize snapshot to JSON
            snapshot_json = json.dumps(
                snapshot.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
                default=str,
            )

            # Upload to S3 with SSE-KMS encryption
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=snapshot_json,
                ContentType="application/json",
                ServerSideEncryption="aws:kms",
                Metadata={
                    "snapshot_id": snapshot.snapshot_id,
                    "snapshot_version": snapshot.snapshot_version,
                    "correlation_id": snapshot.correlation_id,
                    "account_id": snapshot.account_id,
                    "checksum": snapshot.checksum or "",
                },
            )

            s3_uri = f"s3://{bucket_name}/{s3_key}"
            logger.info(
                "Snapshot persisted to S3",
                s3_uri=s3_uri,
                snapshot_id=snapshot.snapshot_id,
                checksum=snapshot.checksum,
            )

            return s3_uri

        except Exception as e:
            logger.error(
                f"Failed to persist snapshot to S3: {e}",
                snapshot_id=snapshot.snapshot_id,
                bucket_name=bucket_name,
            )
            return None
