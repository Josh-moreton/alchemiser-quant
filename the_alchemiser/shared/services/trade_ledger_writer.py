#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trade Ledger Writer Service for Execution Integration.

This module provides a service that converts execution results into trade ledger
entries and persists them with proper idempotency and correlation tracking.
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from ..config.symbols_config import classify_symbol
from ..dto.execution_report_dto import ExecutedOrder
from ..dto.trade_ledger_dto import AssetType, TradeLedgerEntry, TradeSide
from ..persistence.trade_ledger_factory import get_default_trade_ledger
from ..protocols.trade_ledger import TradeLedger

logger = logging.getLogger(__name__)


class TradeLedgerWriter:
    """Service for writing execution results to the trade ledger."""

    def __init__(self, trade_ledger: TradeLedger | None = None) -> None:
        """Initialize the trade ledger writer.

        Args:
            trade_ledger: Trade ledger implementation (uses factory if None)

        """
        self.trade_ledger = trade_ledger or get_default_trade_ledger()

    def record_execution(
        self,
        executed_order: ExecutedOrder,
        *,
        strategy_name: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        account_id: str | None = None,
    ) -> None:
        """Record a single executed order in the trade ledger.

        Args:
            executed_order: Executed order details
            strategy_name: Strategy that generated this trade
            correlation_id: Workflow correlation identifier
            causation_id: Causation identifier for chaining
            account_id: Trading account identifier

        Raises:
            ValueError: If required data is missing or invalid
            IOError: If ledger write fails

        """
        try:
            # Only record if order was actually filled
            if executed_order.filled_quantity <= 0:
                logger.debug(f"Skipping unfilled order {executed_order.order_id}")
                return

            # Convert execution to trade ledger entry
            entry = self._convert_to_ledger_entry(
                executed_order,
                strategy_name=strategy_name,
                correlation_id=correlation_id,
                causation_id=causation_id,
                account_id=account_id,
            )

            # Record in trade ledger
            self.trade_ledger.upsert(entry)

            logger.info(
                f"Recorded trade ledger entry {entry.ledger_id} for "
                f"{entry.strategy_name} {entry.side.value} {entry.quantity} {entry.symbol}"
            )

        except Exception as e:
            logger.error(f"Failed to record execution in trade ledger: {e}")
            raise

    def record_executions(
        self,
        executed_orders: list[ExecutedOrder],
        *,
        strategy_name: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        account_id: str | None = None,
    ) -> None:
        """Record multiple executed orders in the trade ledger.

        Args:
            executed_orders: List of executed order details
            strategy_name: Strategy that generated these trades
            correlation_id: Workflow correlation identifier
            causation_id: Causation identifier for chaining
            account_id: Trading account identifier

        Raises:
            ValueError: If required data is missing or invalid
            IOError: If ledger write fails

        """
        try:
            entries = []

            for executed_order in executed_orders:
                # Only record if order was actually filled
                if executed_order.filled_quantity <= 0:
                    logger.debug(f"Skipping unfilled order {executed_order.order_id}")
                    continue

                entry = self._convert_to_ledger_entry(
                    executed_order,
                    strategy_name=strategy_name,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    account_id=account_id,
                )
                entries.append(entry)

            if entries:
                # Batch write to trade ledger
                self.trade_ledger.upsert_many(entries)

                logger.info(f"Recorded {len(entries)} trade ledger entries for {strategy_name}")
            else:
                logger.debug("No filled orders to record in trade ledger")

        except Exception as e:
            logger.error(f"Failed to record executions in trade ledger: {e}")
            raise

    def _convert_to_ledger_entry(
        self,
        executed_order: ExecutedOrder,
        *,
        strategy_name: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        account_id: str | None = None,
    ) -> TradeLedgerEntry:
        """Convert executed order to trade ledger entry.

        Args:
            executed_order: Executed order details
            strategy_name: Strategy that generated this trade
            correlation_id: Workflow correlation identifier
            causation_id: Causation identifier for chaining
            account_id: Trading account identifier

        Returns:
            Trade ledger entry

        Raises:
            ValueError: If conversion fails due to invalid data

        """
        # Generate unique identifiers
        ledger_id = str(uuid.uuid4())
        event_id = f"execution-{executed_order.order_id}-{ledger_id[:8]}"

        # Use provided IDs or generate new ones
        correlation_id = correlation_id or str(uuid.uuid4())
        causation_id = causation_id or event_id

        # Determine strategy name (fallback to default if not provided)
        final_strategy_name = strategy_name or "default"

        # Convert trade side
        try:
            side = TradeSide(executed_order.action.upper())
        except ValueError:
            raise ValueError(f"Invalid trade side: {executed_order.action}")

        # Estimate asset type (uses shared symbol classification)
        asset_type_str = classify_symbol(executed_order.symbol)
        asset_type = AssetType(asset_type_str) if asset_type_str else None

        # Calculate fees (if available)
        fees = executed_order.fees or Decimal("0")
        if executed_order.commission:
            fees += executed_order.commission

        return TradeLedgerEntry(
            # Unique identifiers
            ledger_id=ledger_id,
            event_id=event_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            # Strategy attribution
            strategy_name=final_strategy_name,
            # Instrument identification
            symbol=executed_order.symbol,
            asset_type=asset_type,
            # Execution details
            side=side,
            quantity=executed_order.filled_quantity,
            price=executed_order.price,
            fees=fees,
            timestamp=executed_order.execution_timestamp,
            # Broker references
            order_id=executed_order.order_id,
            client_order_id=None,  # Not available in ExecutedOrder
            fill_id=None,  # Would need to be provided by broker API
            # Account and venue context
            account_id=account_id,
            venue="ALPACA",  # Hardcoded for now since we only support Alpaca
            # Metadata
            schema_version=1,
            source="execution_v2.core",
            notes=(executed_order.error_message if executed_order.error_message else None),
        )
