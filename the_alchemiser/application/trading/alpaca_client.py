#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

DEPRECATED: Alpaca Client - Moved to Infrastructure Layer.

This module now redirects to the proper TradingClientFacade for backward compatibility.
The actual implementation has been moved to infrastructure/alpaca/alpaca_gateway.py
to properly separate infrastructure concerns from application logic.

Please update imports to use:
    from the_alchemiser.application.trading.trading_client_facade import TradingClientFacade

Migration path:
    Old: AlpacaClient(alpaca_manager, data_provider)
    New: TradingClientFacade(alpaca_manager, data_provider)
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.application.execution.smart_execution import (
        DataProvider as ExecDataProvider,
    )

from the_alchemiser.application.trading.trading_client_facade import TradingClientFacade
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager


class AlpacaClient(TradingClientFacade):
    """DEPRECATED: Redirects to TradingClientFacade for backward compatibility.
    
    This class has been moved to infrastructure layer for proper separation of concerns.
    Use TradingClientFacade directly or update to use infrastructure gateways.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        data_provider: ExecDataProvider,
        validate_buying_power: bool = False,
    ) -> None:
        """Initialize with backward compatibility warning."""
        warnings.warn(
            "AlpacaClient is deprecated. Use TradingClientFacade from "
            "the_alchemiser.application.trading.trading_client_facade instead. "
            "Infrastructure logic has been moved to infrastructure/alpaca/alpaca_gateway.py",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(alpaca_manager, data_provider, validate_buying_power)
