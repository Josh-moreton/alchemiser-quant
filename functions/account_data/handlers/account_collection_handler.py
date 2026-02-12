"""Business Unit: account_data | Status: current.

Handler for three-phase account data collection from Alpaca.

Phases:
    1. Account snapshot   -> ACCOUNT#<id> / SNAPSHOT#<ts>
    2. Positions snapshot  -> POSITIONS#<id> / SNAPSHOT#<ts>
    3. PnL history (1 yr)  -> PNL#<id> / DATE#<YYYY-MM-DD>
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import boto3
from dynamodb_writer import (
    update_latest_pointer,
    write_account_registry,
    write_account_snapshot,
    write_pnl_records,
    write_positions_snapshot,
)

from the_alchemiser.shared.brokers.alpaca_manager import (
    AlpacaManager,
    create_alpaca_manager,
)
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.pnl_service import PnLService

logger = get_logger(__name__)

# DynamoDB resource (re-used across invocations)
dynamodb = boto3.resource("dynamodb")


class AccountCollectionHandler:
    """Collects account data from Alpaca and persists to DynamoDB."""

    def handle(
        self,
        table_name: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Run three-phase account data collection.

        Args:
            table_name: DynamoDB table name for account data.
            correlation_id: Workflow correlation ID.

        Returns:
            Response dict with status, phases completed, and any errors.

        """
        timestamp = datetime.now(UTC).isoformat()
        table = dynamodb.Table(table_name)

        try:
            alpaca_manager, account_service = self._create_alpaca_clients()
        except ConfigurationError as exc:
            logger.error(
                "Alpaca configuration error",
                extra={"correlation_id": correlation_id, "error": str(exc)},
            )
            return {"statusCode": 500, "body": {"status": "error", "error": str(exc)}}

        phases: dict[str, str] = {}
        account_id = ""

        self._collect_account_snapshot(
            table,
            account_service,
            timestamp,
            correlation_id,
            phases,
        )
        account_id = phases.get("_account_id", "")

        self._collect_positions_snapshot(
            table,
            account_service,
            account_id,
            timestamp,
            correlation_id,
            phases,
        )

        self._collect_pnl_history(
            table,
            alpaca_manager,
            account_id,
            correlation_id,
            phases,
        )

        # Remove internal tracking key
        phases.pop("_account_id", None)

        all_success = all(v == "success" for v in phases.values())
        status = "success" if all_success else "partial_failure"
        status_code = 200 if all_success else 207

        logger.info(
            "Account data Lambda completed",
            extra={
                "correlation_id": correlation_id,
                "status": status,
                "phases": phases,
                "account_id": account_id,
            },
        )

        return {
            "statusCode": status_code,
            "body": {
                "status": status,
                "account_id": account_id,
                "timestamp": timestamp,
                "phases": phases,
            },
        }

    def _collect_account_snapshot(
        self,
        table: Any,
        account_service: Any,
        timestamp: str,
        correlation_id: str,
        phases: dict[str, str],
    ) -> None:
        """Phase 1: Account snapshot."""
        try:
            account_dict = account_service.get_account_dict()
            if account_dict:
                account_id = str(account_dict.get("id", "unknown"))
                write_account_snapshot(table, account_id, account_dict, timestamp)
                update_latest_pointer(table, account_id, "ACCOUNT", timestamp)
                write_account_registry(table, account_id, timestamp)
                phases["account_snapshot"] = "success"
                phases["_account_id"] = account_id
                logger.info(
                    "Phase 1 complete: account snapshot",
                    extra={"correlation_id": correlation_id, "account_id": account_id},
                )
            else:
                phases["account_snapshot"] = "skipped_no_data"
                logger.warning(
                    "Phase 1 skipped: no account data returned",
                    extra={"correlation_id": correlation_id},
                )
        except Exception as exc:
            phases["account_snapshot"] = f"error: {exc}"
            logger.error(
                "Phase 1 failed: account snapshot",
                extra={"correlation_id": correlation_id, "error": str(exc)},
                exc_info=True,
            )

    def _collect_positions_snapshot(
        self,
        table: Any,
        account_service: Any,
        account_id: str,
        timestamp: str,
        correlation_id: str,
        phases: dict[str, str],
    ) -> None:
        """Phase 2: Positions snapshot."""
        try:
            positions = account_service.get_positions()
            if account_id:
                position_dicts = self._serialise_positions(positions)
                write_positions_snapshot(table, account_id, position_dicts, timestamp)
                update_latest_pointer(table, account_id, "POSITIONS", timestamp)
                phases["positions_snapshot"] = "success"
                logger.info(
                    "Phase 2 complete: positions snapshot",
                    extra={
                        "correlation_id": correlation_id,
                        "position_count": len(position_dicts),
                    },
                )
            else:
                phases["positions_snapshot"] = "skipped_no_account_id"
        except Exception as exc:
            phases["positions_snapshot"] = f"error: {exc}"
            logger.error(
                "Phase 2 failed: positions snapshot",
                extra={"correlation_id": correlation_id, "error": str(exc)},
                exc_info=True,
            )

    def _collect_pnl_history(
        self,
        table: Any,
        alpaca_manager: AlpacaManager,
        account_id: str,
        correlation_id: str,
        phases: dict[str, str],
    ) -> None:
        """Phase 3: PnL history (1 year)."""
        try:
            if account_id:
                pnl_service = PnLService(
                    alpaca_manager=alpaca_manager,
                    correlation_id=correlation_id,
                )
                daily_records, deposits_by_date = pnl_service.get_all_daily_records(period="1A")
                active_records = [r for r in daily_records if r.equity > 0]

                write_pnl_records(table, account_id, active_records)
                phases["pnl_history"] = "success"
                logger.info(
                    "Phase 3 complete: PnL history",
                    extra={
                        "correlation_id": correlation_id,
                        "total_records": len(daily_records),
                        "active_records": len(active_records),
                        "deposits_found": len(deposits_by_date),
                    },
                )
            else:
                phases["pnl_history"] = "skipped_no_account_id"
        except Exception as exc:
            phases["pnl_history"] = f"error: {exc}"
            logger.error(
                "Phase 3 failed: PnL history",
                extra={"correlation_id": correlation_id, "error": str(exc)},
                exc_info=True,
            )

    def _create_alpaca_clients(self) -> tuple[AlpacaManager, Any]:
        """Create Alpaca manager and account service from environment config.

        Returns:
            Tuple of (AlpacaManager, AlpacaAccountService).

        Raises:
            ConfigurationError: If API keys are missing.

        """
        from the_alchemiser.shared.services.alpaca_account_service import (
            AlpacaAccountService,
        )

        api_key, secret_key, endpoint = get_alpaca_keys()
        if not api_key or not secret_key:
            raise ConfigurationError(
                "Alpaca API keys not found in configuration",
                config_key="ALPACA__KEY/ALPACA__SECRET",
            )

        paper = True
        if endpoint:
            ep_lower = endpoint.lower()
            if "api.alpaca.markets" in ep_lower and "paper" not in ep_lower:
                paper = False

        manager = create_alpaca_manager(api_key=api_key, secret_key=secret_key, paper=paper)

        from alpaca.trading.client import TradingClient

        trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
        account_service = AlpacaAccountService(trading_client)

        return manager, account_service

    def _serialise_positions(self, positions: list[Any]) -> list[dict[str, Any]]:
        """Convert Alpaca Position SDK objects to plain dicts for storage."""
        result: list[dict[str, Any]] = []
        for pos in positions:
            result.append(
                {
                    "symbol": str(getattr(pos, "symbol", "")),
                    "qty": str(getattr(pos, "qty", "0")),
                    "avg_entry_price": str(getattr(pos, "avg_entry_price", "0")),
                    "current_price": str(getattr(pos, "current_price", "0")),
                    "market_value": str(getattr(pos, "market_value", "0")),
                    "cost_basis": str(getattr(pos, "cost_basis", "0")),
                    "unrealized_pl": str(getattr(pos, "unrealized_pl", "0")),
                    "unrealized_plpc": str(getattr(pos, "unrealized_plpc", "0")),
                    "side": str(getattr(pos, "side", "long")),
                    "asset_class": str(getattr(pos, "asset_class", "us_equity")),
                }
            )
        return result
