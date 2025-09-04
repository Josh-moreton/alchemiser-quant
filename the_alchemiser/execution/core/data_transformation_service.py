"""Business Unit: execution | Status: current

Data transformation service handling DTO mappings and data transformations.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.brokers.alpaca import AlpacaManager
from the_alchemiser.execution.mappers.account_mapping import to_money_usd
from the_alchemiser.execution.mappers.trading_service_dto_mapping import (
    dict_to_market_status_dto,
    dict_to_multi_symbol_quotes_dto,
    dict_to_position_metrics_dto,
    dict_to_price_dto,
    dict_to_spread_analysis_dto,
    list_to_enriched_positions_dto,
)
from the_alchemiser.portfolio.mappers.position_mapping import alpaca_position_to_summary
from the_alchemiser.portfolio.schemas.positions import (
    PortfolioValueDTO,
    PositionMetricsDTO,
)
from the_alchemiser.shared.schemas.enriched_data import EnrichedPositionsDTO
from the_alchemiser.shared.schemas.market_data import (
    MarketStatusDTO,
    MultiSymbolQuotesDTO,
    PriceDTO,
    PriceHistoryDTO,
    SpreadAnalysisDTO,
)
from the_alchemiser.shared.utils.decorators import translate_trading_errors
from the_alchemiser.strategy.data.market_data_service import MarketDataService


class DataTransformationService:
    """Service responsible for data transformations and DTO mappings.
    
    Handles market data operations, position data transformations, and complex DTO mappings.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize the data transformation service.

        Args:
            alpaca_manager: The Alpaca manager for broker operations
        """
        self.logger = logging.getLogger(__name__)
        self.alpaca_manager = alpaca_manager
        self.market_data = MarketDataService(alpaca_manager)

    def get_latest_price(self, symbol: str, validate: bool = True) -> PriceDTO:
        """Get latest price with validation and caching."""
        try:
            price = self.market_data.get_validated_price(symbol)
            if price is not None:
                price_dict = {"success": True, "symbol": symbol, "price": price}
                return dict_to_price_dto(price_dict)
            return PriceDTO(
                success=False,
                symbol=symbol,
                error=f"Could not get price for {symbol}",
            )
        except Exception as e:
            return PriceDTO(success=False, symbol=symbol, error=str(e))

    def get_price_history(
        self,
        symbol: str,
        timeframe: str = "1Day",
        limit: int = 100,
        validate: bool = True,
    ) -> PriceHistoryDTO:
        """Get price history (not directly available - use AlpacaManager directly)."""
        return PriceHistoryDTO(
            success=False,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            error="Price history queries not available in enhanced services. Use AlpacaManager directly.",
        )

    def analyze_spread(self, symbol: str) -> SpreadAnalysisDTO:
        """Analyze bid-ask spread for a symbol."""
        try:
            spread_data = self.market_data.get_spread_analysis(symbol)
            if spread_data:
                spread_dict = {
                    "success": True,
                    "symbol": symbol,
                    "spread_analysis": spread_data,
                }
                return dict_to_spread_analysis_dto(spread_dict)
            return SpreadAnalysisDTO(
                success=False,
                symbol=symbol,
                error=f"Could not analyze spread for {symbol}",
            )
        except Exception as e:
            return SpreadAnalysisDTO(success=False, symbol=symbol, error=str(e))

    def get_market_status(self) -> MarketStatusDTO:
        """Get current market status."""
        try:
            is_open = self.market_data.is_market_hours()
            market_dict = {"success": True, "market_open": is_open}
            return dict_to_market_status_dto(market_dict)
        except Exception as e:
            return MarketStatusDTO(success=False, error=str(e))

    def get_multi_symbol_quotes(self, symbols: list[str]) -> MultiSymbolQuotesDTO:
        """Get quotes for multiple symbols."""
        try:
            quotes_dict = {"success": True, "symbols": symbols, "quotes": {}}
            # Note: This would need implementation in MarketDataService
            return dict_to_multi_symbol_quotes_dto(quotes_dict)
        except Exception as e:
            return MultiSymbolQuotesDTO(success=False, symbols=symbols, error=str(e))

    def get_all_positions(self) -> EnrichedPositionsDTO:
        """Get all positions from the underlying repository."""
        try:
            raw_positions = self.alpaca_manager.get_all_positions()
            # Convert to enriched format
            enriched = []
            for position in raw_positions:
                summary = alpaca_position_to_summary(position)
                enriched.append(
                    {
                        "raw": position,
                        "summary": (
                            summary.model_dump() if hasattr(summary, "model_dump") else summary
                        ),
                    }
                )
            return list_to_enriched_positions_dto(enriched)
        except Exception as e:
            return EnrichedPositionsDTO(success=False, positions=[], error=str(e))

    @translate_trading_errors(
        default_return=EnrichedPositionsDTO(
            success=False, positions=[], error="positions unavailable"
        )
    )
    def get_positions_enriched(self) -> EnrichedPositionsDTO:
        """Enriched positions list with typed domain objects.

        Returns list of {"raw": pos, "summary": PositionSummary-as-dict}
        """
        try:
            raw_positions = self.alpaca_manager.get_all_positions()

            # Always return enriched typed path (using typed domain)
            enriched: list[dict[str, Any]] = []
            for p in raw_positions:
                s = alpaca_position_to_summary(p)
                enriched.append(
                    {
                        "raw": p,
                        "summary": {
                            "symbol": s.symbol,
                            "qty": float(s.qty),
                            "avg_entry_price": float(s.avg_entry_price),
                            "current_price": float(s.current_price),
                            "market_value": float(s.market_value),
                            "unrealized_pl": float(s.unrealized_pl),
                            "unrealized_plpc": float(s.unrealized_plpc),
                        },
                    }
                )

            return list_to_enriched_positions_dto(enriched)
        except Exception as e:
            return EnrichedPositionsDTO(success=False, positions=[], error=str(e))

    def get_portfolio_value(self) -> PortfolioValueDTO:
        """Get total portfolio value with typed domain objects."""
        raw = self.alpaca_manager.get_portfolio_value()
        money = to_money_usd(raw)
        return PortfolioValueDTO(value=Decimal(str(raw)), money=money)

    def calculate_position_metrics(self) -> PositionMetricsDTO:
        """Calculate comprehensive position metrics and analytics."""
        try:
            positions = self.alpaca_manager.get_all_positions()
            # Calculate metrics
            total_value = sum(float(pos.market_value) for pos in positions if hasattr(pos, "market_value"))
            largest_positions = sorted(
                positions,
                key=lambda p: float(getattr(p, "market_value", 0)),
                reverse=True,
            )[:5]

            metrics_dict = {
                "success": True,
                "total_positions": len(positions),
                "total_value": total_value,
                "largest_positions": [
                    {
                        "symbol": pos.symbol,
                        "weight": getattr(pos, "weight_percent", 0),
                        "value": getattr(pos, "market_value", 0),
                    }
                    for pos in largest_positions
                ],
            }
            return dict_to_position_metrics_dto(metrics_dict)
        except Exception as e:
            return PositionMetricsDTO(success=False, error=str(e))