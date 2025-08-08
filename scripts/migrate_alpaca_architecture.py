#!/usr/bin/env python3
"""
Alpaca Architecture Migration Script

This script implements Phase 1 of the architecture redesign:
1. Creates the new directory structure
2. Implements the core infrastructure adapters
3. Creates domain interfaces and models
4. Sets up dependency injection container

Run this script to begin the migration to the new architecture.
"""

from pathlib import Path


def create_directory_structure():
    """Create the new directory structure for the redesigned architecture."""

    directories = [
        # Infrastructure Layer - Alpaca Adapters
        "the_alchemiser/infrastructure/alpaca",
        "the_alchemiser/infrastructure/alpaca/adapters",
        "the_alchemiser/infrastructure/alpaca/clients",
        "the_alchemiser/infrastructure/alpaca/types",

        # Domain Layer - Interfaces and Models
        "the_alchemiser/domain/interfaces",
        "the_alchemiser/domain/models",

        # Service Layer - Business Logic
        "the_alchemiser/services/trading",
        "the_alchemiser/services/market_data",
        "the_alchemiser/services/account",
        "the_alchemiser/services/shared",

        # Application Layer - High-Level Operations
        "the_alchemiser/application/trading",
        "the_alchemiser/application/strategies",
        "the_alchemiser/application/portfolio",
        "the_alchemiser/application/workflows",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files
        (Path(directory) / "__init__.py").touch(exist_ok=True)

    print("✅ Created new directory structure")


def create_infrastructure_adapters():
    """Create the infrastructure adapters that interface with Alpaca."""

    # Trading Adapter
    trading_adapter_content = '''"""Trading operations adapter for Alpaca API."""

from typing import Any
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.domain.models.orders import Order, OrderRequest
from the_alchemiser.domain.models.positions import Position
from the_alchemiser.infrastructure.alpaca.types.converters import AlpacaConverter


class TradingAdapter(TradingRepository):
    """Alpaca implementation of trading operations."""
    
    def __init__(self, client: TradingClient):
        self._client = client
        self._converter = AlpacaConverter()
    
    def place_order(self, order_request: OrderRequest) -> Order:
        """Place an order through Alpaca."""
        try:
            # Convert domain order request to Alpaca request
            if order_request.order_type == "market":
                alpaca_request = MarketOrderRequest(
                    symbol=order_request.symbol,
                    qty=order_request.quantity,
                    side=OrderSide(order_request.side.upper()),
                    time_in_force=TimeInForce.DAY
                )
            elif order_request.order_type == "limit":
                alpaca_request = LimitOrderRequest(
                    symbol=order_request.symbol,
                    qty=order_request.quantity,
                    side=OrderSide(order_request.side.upper()),
                    time_in_force=TimeInForce.DAY,
                    limit_price=order_request.limit_price
                )
            else:
                raise ValueError(f"Unsupported order type: {order_request.order_type}")
            
            # Execute through Alpaca
            alpaca_order = self._client.submit_order(alpaca_request)
            
            # Convert back to domain model
            return self._converter.convert_alpaca_order_to_domain(alpaca_order)
            
        except Exception as e:
            raise TradingError(f"Failed to place order: {e}") from e
    
    def get_positions(self) -> list[Position]:
        """Get all positions from Alpaca."""
        try:
            alpaca_positions = self._client.get_all_positions()
            return [
                self._converter.convert_alpaca_position_to_domain(pos) 
                for pos in alpaca_positions
            ]
        except Exception as e:
            raise TradingError(f"Failed to get positions: {e}") from e
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        try:
            self._client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            raise TradingError(f"Failed to cancel order {order_id}: {e}") from e
    
    def get_orders(self, status: str | None = None) -> list[Order]:
        """Get orders, optionally filtered by status."""
        try:
            alpaca_orders = self._client.get_orders(
                status=status.upper() if status else None
            )
            return [
                self._converter.convert_alpaca_order_to_domain(order) 
                for order in alpaca_orders
            ]
        except Exception as e:
            raise TradingError(f"Failed to get orders: {e}") from e


class TradingError(Exception):
    """Trading operation error."""
    pass
'''

    # Market Data Adapter
    market_data_adapter_content = '''"""Market data adapter for Alpaca API."""

from datetime import datetime
from typing import Any
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.domain.interfaces.market_data_repository import MarketDataRepository
from the_alchemiser.domain.models.market_data import Quote, HistoricalData
from the_alchemiser.infrastructure.alpaca.types.converters import AlpacaConverter


class MarketDataAdapter(MarketDataRepository):
    """Alpaca implementation of market data operations."""
    
    def __init__(self, client: StockHistoricalDataClient):
        self._client = client
        self._converter = AlpacaConverter()
    
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        try:
            quote = self.get_latest_quote(symbol)
            if quote:
                return (quote.bid + quote.ask) / 2
            return None
        except Exception as e:
            raise MarketDataError(f"Failed to get current price for {symbol}: {e}") from e
    
    def get_latest_quote(self, symbol: str) -> Quote | None:
        """Get latest quote for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            response = self._client.get_stock_latest_quote(request)
            
            if symbol in response:
                alpaca_quote = response[symbol]
                return self._converter.convert_alpaca_quote_to_domain(alpaca_quote)
            
            return None
        except Exception as e:
            raise MarketDataError(f"Failed to get quote for {symbol}: {e}") from e
    
    def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        timeframe: str = "1Day"
    ) -> HistoricalData:
        """Get historical bar data for a symbol."""
        try:
            # Convert timeframe string to Alpaca TimeFrame
            tf_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "Minute"),
                "15Min": TimeFrame(15, "Minute"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day
            }
            
            alpaca_timeframe = tf_map.get(timeframe, TimeFrame.Day)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start,
                end=end
            )
            
            response = self._client.get_stock_bars(request)
            
            if symbol in response:
                bars = response[symbol]
                return self._converter.convert_alpaca_bars_to_domain(bars, symbol)
            
            return HistoricalData(symbol=symbol, bars=[])
            
        except Exception as e:
            raise MarketDataError(f"Failed to get historical data for {symbol}: {e}") from e


class MarketDataError(Exception):
    """Market data operation error."""
    pass
'''

    # Account Adapter
    account_adapter_content = '''"""Account operations adapter for Alpaca API."""

from typing import Any
from alpaca.trading.client import TradingClient

from the_alchemiser.domain.interfaces.account_repository import AccountRepository
from the_alchemiser.domain.models.account import Account, Portfolio
from the_alchemiser.infrastructure.alpaca.types.converters import AlpacaConverter


class AccountAdapter(AccountRepository):
    """Alpaca implementation of account operations."""
    
    def __init__(self, client: TradingClient):
        self._client = client
        self._converter = AlpacaConverter()
    
    def get_account(self) -> Account:
        """Get account information."""
        try:
            alpaca_account = self._client.get_account()
            return self._converter.convert_alpaca_account_to_domain(alpaca_account)
        except Exception as e:
            raise AccountError(f"Failed to get account info: {e}") from e
    
    def get_portfolio(self) -> Portfolio:
        """Get portfolio information."""
        try:
            # Get account info for portfolio value
            account = self.get_account()
            
            # Get positions for holdings
            positions = self._client.get_all_positions()
            
            return Portfolio(
                total_value=account.portfolio_value,
                cash=account.cash,
                buying_power=account.buying_power,
                positions=[
                    self._converter.convert_alpaca_position_to_domain(pos)
                    for pos in positions
                ]
            )
        except Exception as e:
            raise AccountError(f"Failed to get portfolio: {e}") from e


class AccountError(Exception):
    """Account operation error."""
    pass
'''

    # Client Factory
    client_factory_content = '''"""Factory for creating and configuring Alpaca clients."""

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient

from the_alchemiser.infrastructure.alpaca.clients.client_config import ClientConfig


class ClientFactory:
    """Factory for creating Alpaca clients."""
    
    def __init__(self, config: ClientConfig | None = None):
        self._config = config or ClientConfig()
    
    def create_trading_client(self, api_key: str, secret_key: str, paper: bool = True) -> TradingClient:
        """Create a trading client."""
        return TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )
    
    def create_market_data_client(self, api_key: str, secret_key: str) -> StockHistoricalDataClient:
        """Create a market data client."""
        return StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )
'''

    # Client Config
    client_config_content = '''"""Configuration for Alpaca clients."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ClientConfig:
    """Configuration for Alpaca clients."""
    
    # Connection settings
    timeout: int = 30
    retries: int = 3
    
    # Rate limiting
    max_requests_per_minute: int = 200
    
    # Paper trading settings
    paper_trading: bool = True
    
    # Additional client options
    client_options: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for client initialization."""
        return {
            "timeout": self.timeout,
            "retries": self.retries,
            **(self.client_options or {})
        }
'''

    # Write adapter files
    adapters = [
        ("trading_adapter.py", trading_adapter_content),
        ("market_data_adapter.py", market_data_adapter_content),
        ("account_adapter.py", account_adapter_content),
    ]

    for filename, content in adapters:
        path = Path(f"the_alchemiser/infrastructure/alpaca/adapters/{filename}")
        path.write_text(content)

    # Write client files
    clients = [
        ("client_factory.py", client_factory_content),
        ("client_config.py", client_config_content),
    ]

    for filename, content in clients:
        path = Path(f"the_alchemiser/infrastructure/alpaca/clients/{filename}")
        path.write_text(content)

    print("✅ Created infrastructure adapters")


def create_domain_interfaces():
    """Create domain interfaces and models."""

    # Trading Repository Interface
    trading_repository_content = '''"""Trading repository interface."""

from abc import ABC, abstractmethod
from typing import Protocol

from the_alchemiser.domain.models.orders import Order, OrderRequest
from the_alchemiser.domain.models.positions import Position


class TradingRepository(Protocol):
    """Interface for trading operations."""
    
    def place_order(self, order_request: OrderRequest) -> Order:
        """Place an order."""
        ...
    
    def get_positions(self) -> list[Position]:
        """Get all positions."""
        ...
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        ...
    
    def get_orders(self, status: str | None = None) -> list[Order]:
        """Get orders, optionally filtered by status."""
        ...
'''

    # Market Data Repository Interface
    market_data_repository_content = '''"""Market data repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol

from the_alchemiser.domain.models.market_data import Quote, HistoricalData


class MarketDataRepository(Protocol):
    """Interface for market data operations."""
    
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        ...
    
    def get_latest_quote(self, symbol: str) -> Quote | None:
        """Get latest quote for a symbol."""
        ...
    
    def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        timeframe: str = "1Day"
    ) -> HistoricalData:
        """Get historical bar data for a symbol."""
        ...
'''

    # Account Repository Interface
    account_repository_content = '''"""Account repository interface."""

from abc import ABC, abstractmethod
from typing import Protocol

from the_alchemiser.domain.models.account import Account, Portfolio


class AccountRepository(Protocol):
    """Interface for account operations."""
    
    def get_account(self) -> Account:
        """Get account information."""
        ...
    
    def get_portfolio(self) -> Portfolio:
        """Get portfolio information."""
        ...
'''

    # Write interface files
    interfaces = [
        ("trading_repository.py", trading_repository_content),
        ("market_data_repository.py", market_data_repository_content),
        ("account_repository.py", account_repository_content),
    ]

    for filename, content in interfaces:
        path = Path(f"the_alchemiser/domain/interfaces/{filename}")
        path.write_text(content)

    print("✅ Created domain interfaces")


def create_domain_models():
    """Create domain models."""

    # Order Models
    order_models_content = '''"""Order domain models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"


@dataclass
class OrderRequest:
    """Domain model for order requests."""
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str = "day"


@dataclass
class Order:
    """Domain model for orders."""
    id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    status: OrderStatus
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    filled_quantity: Decimal = Decimal("0")
    filled_avg_price: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is active (not terminal state)."""
        return self.status in {OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED}
'''

    # Position Models
    position_models_content = '''"""Position domain models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Position:
    """Domain model for positions."""
    symbol: str
    quantity: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    current_price: Decimal | None = None
    
    @property
    def is_long(self) -> bool:
        """Check if this is a long position."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if this is a short position."""
        return self.quantity < 0
    
    @property
    def average_entry_price(self) -> Decimal:
        """Calculate average entry price."""
        if self.quantity == 0:
            return Decimal("0")
        return self.cost_basis / abs(self.quantity)
'''

    # Market Data Models
    market_data_models_content = '''"""Market data domain models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Quote:
    """Domain model for quotes."""
    symbol: str
    bid: Decimal
    ask: Decimal
    bid_size: int
    ask_size: int
    timestamp: datetime
    
    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        return self.ask - self.bid
    
    @property
    def mid_price(self) -> Decimal:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2


@dataclass
class Bar:
    """Domain model for price bars."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    trade_count: int | None = None
    vwap: Decimal | None = None


@dataclass
class HistoricalData:
    """Domain model for historical data."""
    symbol: str
    bars: list[Bar]
    timeframe: str = "1Day"
    
    @property
    def is_empty(self) -> bool:
        """Check if data is empty."""
        return len(self.bars) == 0
    
    def to_dataframe(self) -> "pd.DataFrame":
        """Convert to pandas DataFrame."""
        import pandas as pd
        
        if self.is_empty:
            return pd.DataFrame()
        
        data = []
        for bar in self.bars:
            data.append({
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": bar.volume,
                "trade_count": bar.trade_count,
                "vwap": float(bar.vwap) if bar.vwap else None
            })
        
        return pd.DataFrame(data).set_index("timestamp")
'''

    # Account Models
    account_models_content = '''"""Account domain models."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.models.positions import Position


@dataclass
class Account:
    """Domain model for account information."""
    id: str
    cash: Decimal
    portfolio_value: Decimal
    buying_power: Decimal
    equity: Decimal
    last_equity: Decimal
    multiplier: Decimal
    initial_margin: Decimal
    maintenance_margin: Decimal
    sma: Decimal  # Special Memorandum Account
    status: str
    currency: str = "USD"
    pattern_day_trader: bool = False
    
    @property
    def net_liquidation_value(self) -> Decimal:
        """Net liquidation value (same as portfolio value)."""
        return self.portfolio_value
    
    @property
    def excess_liquidity(self) -> Decimal:
        """Excess liquidity calculation."""
        return self.equity - self.maintenance_margin


@dataclass
class Portfolio:
    """Domain model for portfolio information."""
    total_value: Decimal
    cash: Decimal
    buying_power: Decimal
    positions: list[Position]
    
    @property
    def positions_value(self) -> Decimal:
        """Total value of all positions."""
        return sum(pos.market_value for pos in self.positions)
    
    @property
    def total_unrealized_pnl(self) -> Decimal:
        """Total unrealized PnL across all positions."""
        return sum(pos.unrealized_pnl for pos in self.positions)
    
    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        for position in self.positions:
            if position.symbol == symbol:
                return position
        return None
'''

    # Type Converters
    converters_content = '''"""Type converters between Alpaca and domain models."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.models.orders import Order, OrderSide, OrderType, OrderStatus
from the_alchemiser.domain.models.positions import Position
from the_alchemiser.domain.models.market_data import Quote, Bar, HistoricalData
from the_alchemiser.domain.models.account import Account


class AlpacaConverter:
    """Converts between Alpaca types and domain models."""
    
    def convert_alpaca_order_to_domain(self, alpaca_order: Any) -> Order:
        """Convert Alpaca order to domain order."""
        return Order(
            id=str(alpaca_order.id),
            symbol=alpaca_order.symbol,
            side=OrderSide(alpaca_order.side.lower()),
            quantity=Decimal(str(alpaca_order.qty)),
            order_type=OrderType(alpaca_order.order_type.lower()),
            status=OrderStatus(alpaca_order.status.lower()),
            limit_price=Decimal(str(alpaca_order.limit_price)) if alpaca_order.limit_price else None,
            stop_price=Decimal(str(alpaca_order.stop_price)) if alpaca_order.stop_price else None,
            filled_quantity=Decimal(str(alpaca_order.filled_qty or 0)),
            filled_avg_price=Decimal(str(alpaca_order.filled_avg_price)) if alpaca_order.filled_avg_price else None,
            created_at=self._parse_datetime(alpaca_order.created_at),
            updated_at=self._parse_datetime(alpaca_order.updated_at)
        )
    
    def convert_alpaca_position_to_domain(self, alpaca_position: Any) -> Position:
        """Convert Alpaca position to domain position."""
        return Position(
            symbol=alpaca_position.symbol,
            quantity=Decimal(str(alpaca_position.qty)),
            market_value=Decimal(str(alpaca_position.market_value)),
            cost_basis=Decimal(str(alpaca_position.cost_basis)),
            unrealized_pnl=Decimal(str(alpaca_position.unrealized_pl)),
            unrealized_pnl_percent=Decimal(str(alpaca_position.unrealized_plpc)),
            current_price=Decimal(str(alpaca_position.current_price)) if alpaca_position.current_price else None
        )
    
    def convert_alpaca_quote_to_domain(self, alpaca_quote: Any) -> Quote:
        """Convert Alpaca quote to domain quote."""
        return Quote(
            symbol=alpaca_quote.symbol if hasattr(alpaca_quote, 'symbol') else "UNKNOWN",
            bid=Decimal(str(alpaca_quote.bid_price)),
            ask=Decimal(str(alpaca_quote.ask_price)),
            bid_size=int(alpaca_quote.bid_size),
            ask_size=int(alpaca_quote.ask_size),
            timestamp=self._parse_datetime(alpaca_quote.timestamp)
        )
    
    def convert_alpaca_bars_to_domain(self, alpaca_bars: Any, symbol: str) -> HistoricalData:
        """Convert Alpaca bars to domain historical data."""
        bars = []
        for bar in alpaca_bars:
            domain_bar = Bar(
                timestamp=self._parse_datetime(bar.timestamp),
                open=Decimal(str(bar.open)),
                high=Decimal(str(bar.high)),
                low=Decimal(str(bar.low)),
                close=Decimal(str(bar.close)),
                volume=int(bar.volume),
                trade_count=int(bar.trade_count) if hasattr(bar, 'trade_count') and bar.trade_count else None,
                vwap=Decimal(str(bar.vwap)) if hasattr(bar, 'vwap') and bar.vwap else None
            )
            bars.append(domain_bar)
        
        return HistoricalData(symbol=symbol, bars=bars)
    
    def convert_alpaca_account_to_domain(self, alpaca_account: Any) -> Account:
        """Convert Alpaca account to domain account."""
        return Account(
            id=str(alpaca_account.id),
            cash=Decimal(str(alpaca_account.cash)),
            portfolio_value=Decimal(str(alpaca_account.portfolio_value)),
            buying_power=Decimal(str(alpaca_account.buying_power)),
            equity=Decimal(str(alpaca_account.equity)),
            last_equity=Decimal(str(alpaca_account.last_equity)),
            multiplier=Decimal(str(alpaca_account.multiplier)),
            initial_margin=Decimal(str(alpaca_account.initial_margin)),
            maintenance_margin=Decimal(str(alpaca_account.maintenance_margin)),
            sma=Decimal(str(alpaca_account.sma)),
            status=str(alpaca_account.status),
            currency=str(alpaca_account.currency),
            pattern_day_trader=bool(alpaca_account.pattern_day_trader)
        )
    
    def _parse_datetime(self, dt: Any) -> datetime:
        """Parse datetime from various formats."""
        if isinstance(dt, datetime):
            return dt
        elif isinstance(dt, str):
            # Handle various string datetime formats
            try:
                return datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return datetime.now()
        else:
            return datetime.now()
'''

    # Write model files
    models = [
        ("orders.py", order_models_content),
        ("positions.py", position_models_content),
        ("market_data.py", market_data_models_content),
        ("account.py", account_models_content),
    ]

    for filename, content in models:
        path = Path(f"the_alchemiser/domain/models/{filename}")
        path.write_text(content)

    # Write converter file
    converter_path = Path("the_alchemiser/infrastructure/alpaca/types/converters.py")
    converter_path.write_text(converters_content)

    print("✅ Created domain models and converters")


def create_service_layer():
    """Create the service layer that orchestrates business logic."""

    # Order Service
    order_service_content = '''"""Order service for business logic orchestration."""

from decimal import Decimal
from typing import Any

from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.domain.models.orders import Order, OrderRequest, OrderSide, OrderType
from the_alchemiser.services.shared.validation_service import ValidationService


class OrderService:
    """Service for order placement and management."""
    
    def __init__(
        self, 
        trading_repo: TradingRepository,
        validation_service: ValidationService
    ):
        self._trading_repo = trading_repo
        self._validation = validation_service
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Order:
        """Place a validated market order."""
        # Create order request
        order_request = OrderRequest(
            symbol=symbol.upper(),
            side=OrderSide(side.lower()),
            quantity=Decimal(str(quantity)),
            order_type=OrderType.MARKET
        )
        
        # Validate order
        self._validation.validate_order_request(order_request)
        
        # Place order through repository
        return self._trading_repo.place_order(order_request)
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float
    ) -> Order:
        """Place a validated limit order."""
        # Create order request
        order_request = OrderRequest(
            symbol=symbol.upper(),
            side=OrderSide(side.lower()),
            quantity=Decimal(str(quantity)),
            order_type=OrderType.LIMIT,
            limit_price=Decimal(str(limit_price))
        )
        
        # Validate order
        self._validation.validate_order_request(order_request)
        
        # Place order through repository
        return self._trading_repo.place_order(order_request)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        return self._trading_repo.cancel_order(order_id)
    
    def get_orders(self, status: str | None = None) -> list[Order]:
        """Get orders, optionally filtered by status."""
        return self._trading_repo.get_orders(status)
    
    def get_active_orders(self) -> list[Order]:
        """Get all active orders."""
        all_orders = self.get_orders()
        return [order for order in all_orders if order.is_active]
'''

    # Position Service
    position_service_content = '''"""Position service for position management."""

from decimal import Decimal

from the_alchemiser.domain.interfaces.trading_repository import TradingRepository
from the_alchemiser.domain.interfaces.market_data_repository import MarketDataRepository
from the_alchemiser.domain.models.positions import Position


class PositionService:
    """Service for position management and validation."""
    
    def __init__(
        self,
        trading_repo: TradingRepository,
        market_data_repo: MarketDataRepository
    ):
        self._trading_repo = trading_repo
        self._market_data_repo = market_data_repo
    
    def get_positions(self) -> list[Position]:
        """Get all current positions."""
        return self._trading_repo.get_positions()
    
    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        positions = self.get_positions()
        for position in positions:
            if position.symbol == symbol:
                return position
        return None
    
    def get_position_value(self, symbol: str) -> Decimal:
        """Get current market value of a position."""
        position = self.get_position(symbol)
        if position:
            return position.market_value
        return Decimal("0")
    
    def can_sell_quantity(self, symbol: str, quantity: float) -> tuple[bool, str]:
        """Check if we can sell the specified quantity."""
        position = self.get_position(symbol)
        
        if not position:
            return False, f"No position found for {symbol}"
        
        if position.quantity <= 0:
            return False, f"No long position in {symbol}"
        
        requested_quantity = Decimal(str(quantity))
        if requested_quantity > position.quantity:
            return False, f"Insufficient shares: have {position.quantity}, requested {requested_quantity}"
        
        return True, "OK"
    
    def get_portfolio_value(self) -> Decimal:
        """Get total portfolio value."""
        positions = self.get_positions()
        return sum(pos.market_value for pos in positions)
    
    def get_unrealized_pnl(self) -> Decimal:
        """Get total unrealized PnL."""
        positions = self.get_positions()
        return sum(pos.unrealized_pnl for pos in positions)
'''

    # Price Service
    price_service_content = '''"""Price service for market data management."""

from datetime import datetime
from typing import Any
import asyncio

from the_alchemiser.domain.interfaces.market_data_repository import MarketDataRepository
from the_alchemiser.domain.models.market_data import Quote, HistoricalData
from the_alchemiser.services.shared.cache_service import CacheService


class PriceService:
    """Service for price and market data management."""
    
    def __init__(
        self,
        market_data_repo: MarketDataRepository,
        cache_service: CacheService
    ):
        self._market_data_repo = market_data_repo
        self._cache = cache_service
    
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol with caching."""
        cache_key = f"price:{symbol}"
        
        # Check cache first
        cached_price = self._cache.get(cache_key)
        if cached_price is not None:
            return cached_price
        
        # Fetch from repository
        price = self._market_data_repo.get_current_price(symbol)
        
        # Cache for 10 seconds
        if price is not None:
            self._cache.set(cache_key, price, ttl=10)
        
        return price
    
    async def get_current_prices(self, symbols: list[str]) -> dict[str, float | None]:
        """Get current prices for multiple symbols concurrently."""
        tasks = [self._get_price_async(symbol) for symbol in symbols]
        prices = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = {}
        for symbol, price in zip(symbols, prices):
            if isinstance(price, Exception):
                result[symbol] = None
            else:
                result[symbol] = price
        
        return result
    
    async def _get_price_async(self, symbol: str) -> float | None:
        """Async wrapper for getting a single price."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_current_price, symbol)
    
    def get_latest_quote(self, symbol: str) -> Quote | None:
        """Get latest quote for a symbol."""
        return self._market_data_repo.get_latest_quote(symbol)
    
    def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        timeframe: str = "1Day"
    ) -> HistoricalData:
        """Get historical data for a symbol."""
        return self._market_data_repo.get_historical_data(symbol, start, end, timeframe)
'''

    # Validation Service
    validation_service_content = '''"""Validation service for cross-cutting validation logic."""

from decimal import Decimal

from the_alchemiser.domain.models.orders import OrderRequest


class ValidationService:
    """Service for order and business logic validation."""
    
    def __init__(self):
        # Validation rules configuration
        self.min_order_value = Decimal("1.00")  # $1 minimum
        self.max_order_value = Decimal("100000.00")  # $100k maximum
        self.min_quantity = Decimal("0.001")  # Minimum fractional shares
        self.max_quantity = Decimal("10000")  # Maximum shares per order
    
    def validate_order_request(self, order_request: OrderRequest) -> None:
        """Validate an order request."""
        self._validate_symbol(order_request.symbol)
        self._validate_quantity(order_request.quantity)
        self._validate_prices(order_request)
    
    def _validate_symbol(self, symbol: str) -> None:
        """Validate symbol format."""
        if not symbol:
            raise ValidationError("Symbol cannot be empty")
        
        if not symbol.isalpha():
            raise ValidationError("Symbol must contain only letters")
        
        if len(symbol) > 10:
            raise ValidationError("Symbol too long (max 10 characters)")
    
    def _validate_quantity(self, quantity: Decimal) -> None:
        """Validate order quantity."""
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        if quantity < self.min_quantity:
            raise ValidationError(f"Quantity below minimum {self.min_quantity}")
        
        if quantity > self.max_quantity:
            raise ValidationError(f"Quantity above maximum {self.max_quantity}")
    
    def _validate_prices(self, order_request: OrderRequest) -> None:
        """Validate order prices."""
        if order_request.limit_price is not None:
            if order_request.limit_price <= 0:
                raise ValidationError("Limit price must be positive")
        
        if order_request.stop_price is not None:
            if order_request.stop_price <= 0:
                raise ValidationError("Stop price must be positive")
    
    def validate_order_value(self, quantity: Decimal, price: Decimal) -> None:
        """Validate total order value."""
        total_value = quantity * price
        
        if total_value < self.min_order_value:
            raise ValidationError(f"Order value ${total_value} below minimum ${self.min_order_value}")
        
        if total_value > self.max_order_value:
            raise ValidationError(f"Order value ${total_value} above maximum ${self.max_order_value}")


class ValidationError(Exception):
    """Validation error."""
    pass
'''

    # Cache Service
    cache_service_content = '''"""Cache service for performance optimization."""

import time
from typing import Any, TypeVar, Generic

T = TypeVar('T')


class CacheService(Generic[T]):
    """Service for caching frequently accessed data."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: dict[str, tuple[T, float]] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> T | None:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self._default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
'''

    # Write service files
    services = [
        ("trading/order_service.py", order_service_content),
        ("trading/position_service.py", position_service_content),
        ("market_data/price_service.py", price_service_content),
        ("shared/validation_service.py", validation_service_content),
        ("shared/cache_service.py", cache_service_content),
    ]

    for filepath, content in services:
        path = Path(f"the_alchemiser/services/{filepath}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    print("✅ Created service layer")


def create_dependency_injection():
    """Create dependency injection container."""

    container_content = '''"""Dependency injection container for the application."""

from dependency_injector import containers, providers

from the_alchemiser.infrastructure.alpaca.clients.client_factory import ClientFactory
from the_alchemiser.infrastructure.alpaca.clients.client_config import ClientConfig
from the_alchemiser.infrastructure.alpaca.adapters.trading_adapter import TradingAdapter
from the_alchemiser.infrastructure.alpaca.adapters.market_data_adapter import MarketDataAdapter
from the_alchemiser.infrastructure.alpaca.adapters.account_adapter import AccountAdapter

from the_alchemiser.services.trading.order_service import OrderService
from the_alchemiser.services.trading.position_service import PositionService
from the_alchemiser.services.market_data.price_service import PriceService
from the_alchemiser.services.shared.validation_service import ValidationService
from the_alchemiser.services.shared.cache_service import CacheService


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Infrastructure - Client Configuration
    client_config = providers.Singleton(ClientConfig)
    client_factory = providers.Singleton(ClientFactory, client_config)
    
    # Infrastructure - Alpaca Clients
    trading_client = providers.Factory(
        client_factory.provided.create_trading_client,
        api_key=config.alpaca.api_key,
        secret_key=config.alpaca.secret_key,
        paper=config.alpaca.paper_trading
    )
    
    market_data_client = providers.Factory(
        client_factory.provided.create_market_data_client,
        api_key=config.alpaca.api_key,
        secret_key=config.alpaca.secret_key
    )
    
    # Infrastructure - Adapters
    trading_adapter = providers.Factory(TradingAdapter, trading_client)
    market_data_adapter = providers.Factory(MarketDataAdapter, market_data_client)
    account_adapter = providers.Factory(AccountAdapter, trading_client)
    
    # Services - Shared
    cache_service = providers.Singleton(CacheService)
    validation_service = providers.Singleton(ValidationService)
    
    # Services - Business Logic
    order_service = providers.Factory(
        OrderService,
        trading_repo=trading_adapter,
        validation_service=validation_service
    )
    
    position_service = providers.Factory(
        PositionService,
        trading_repo=trading_adapter,
        market_data_repo=market_data_adapter
    )
    
    price_service = providers.Factory(
        PriceService,
        market_data_repo=market_data_adapter,
        cache_service=cache_service
    )


# Global container instance
container = Container()
'''

    path = Path("the_alchemiser/container.py")
    path.write_text(container_content)

    print("✅ Created dependency injection container")


def create_migration_documentation():
    """Create documentation for the migration."""

    migration_doc_content = '''# Migration Documentation

## Overview

This document describes the migration from the old scattered Alpaca architecture to the new clean, modular design.

## What Changed

### Directory Structure

```
Old Structure:
├── services/
│   ├── account_service.py          # Mixed concerns
│   ├── trading_client_service.py   # Direct Alpaca dependency
│   ├── market_data_client.py       # Direct Alpaca dependency
│   ├── price_service.py            # Mixed with streaming
│   └── position_manager.py         # Business logic + API calls
├── application/
│   └── alpaca_client.py            # Monolithic trading client
└── infrastructure/
    └── data_providers/
        └── unified_data_provider_facade.py  # God object

New Structure:
├── infrastructure/alpaca/          # All Alpaca interactions isolated
│   ├── adapters/                   # Clean adapter pattern
│   ├── clients/                    # Client factory and config
│   └── types/                      # Type conversions
├── domain/
│   ├── interfaces/                 # Abstract repository contracts
│   └── models/                     # Pure domain models
├── services/
│   ├── trading/                    # Trading business logic
│   ├── market_data/               # Market data business logic
│   ├── account/                   # Account business logic
│   └── shared/                    # Cross-cutting concerns
└── application/
    ├── trading/                   # High-level trading operations
    ├── portfolio/                 # Portfolio management
    └── workflows/                 # Complete business workflows
```

### Key Changes

1. **Alpaca Isolation**: All Alpaca API calls now go through dedicated adapters
2. **Clear Separation**: Trading, market data, and account operations are separate
3. **Domain Models**: Clean, typed domain objects instead of raw Alpaca types
4. **Repository Pattern**: Abstract interfaces enable easy testing and mocking
5. **Dependency Injection**: Clean dependency management through container
6. **Type Safety**: Comprehensive typing throughout the stack

## Migration Guide

### For Developers

#### Before (Old Way)
```python
# Direct Alpaca usage scattered everywhere
from alpaca.trading.client import TradingClient
from the_alchemiser.services.trading_client_service import TradingClientService

client = TradingClient(api_key, secret_key)
positions = client.get_all_positions()
```

#### After (New Way)
```python
# Clean service layer with dependency injection
from the_alchemiser.container import container

position_service = container.position_service()
positions = position_service.get_positions()
```

### Import Changes

| Old Import | New Import |
|------------|------------|
| `from the_alchemiser.services.account_service import AccountService` | `from the_alchemiser.services.account.account_service import AccountService` |
| `from the_alchemiser.services.trading_client_service import TradingClientService` | `from the_alchemiser.infrastructure.alpaca.adapters.trading_adapter import TradingAdapter` |
| `from the_alchemiser.services.market_data_client import MarketDataClient` | `from the_alchemiser.infrastructure.alpaca.adapters.market_data_adapter import MarketDataAdapter` |
| `from the_alchemiser.services.price_service import ModernPriceFetchingService` | `from the_alchemiser.services.market_data.price_service import PriceService` |
| `from the_alchemiser.application.alpaca_client import AlpacaClient` | `from the_alchemiser.application.trading.trading_engine import TradingEngine` |
| `from the_alchemiser.services.position_manager import PositionManager` | `from the_alchemiser.services.trading.position_service import PositionService` |

### API Changes

#### Order Placement

**Before:**
```python
alpaca_client = AlpacaClient(trading_client, data_provider)
order_id = alpaca_client.place_market_order('AAPL', OrderSide.BUY, qty=10)
```

**After:**
```python
order_service = container.order_service()
order = order_service.place_market_order('AAPL', 'buy', 10.0)
```

#### Position Management

**Before:**
```python
position_manager = PositionManager(trading_client, data_provider)
positions = position_manager.get_current_positions()
```

**After:**
```python
position_service = container.position_service()
positions = position_service.get_positions()
```

#### Price Data

**Before:**
```python
price_service = ModernPriceFetchingService(market_data_client, streaming_service)
price = price_service.get_current_price('AAPL')
```

**After:**
```python
price_service = container.price_service()
price = price_service.get_current_price('AAPL')
```

## Benefits

1. **Testability**: Easy to mock dependencies for unit testing
2. **Maintainability**: Changes to Alpaca API only affect adapter layer
3. **Performance**: Centralized caching and connection management
4. **Type Safety**: Strong typing with domain models
5. **Extensibility**: Easy to add new brokers or data sources
6. **Documentation**: Clear contracts through interfaces

## Testing

### Unit Testing

**Before:**
```python
# Hard to test due to direct Alpaca dependencies
def test_order_placement():
    # Would need to mock Alpaca client directly
    pass
```

**After:**
```python
# Easy to test with mock repositories
def test_order_placement():
    mock_trading_repo = Mock(spec=TradingRepository)
    mock_validation_service = Mock(spec=ValidationService)
    
    order_service = OrderService(mock_trading_repo, mock_validation_service)
    order = order_service.place_market_order('AAPL', 'buy', 10.0)
    
    mock_trading_repo.place_order.assert_called_once()
```

### Integration Testing

**Before:**
```python
# Required real Alpaca credentials for integration tests
```

**After:**
```python
# Can use test implementations of repositories
def test_integration():
    test_container = Container()
    test_container.config.from_dict({
        'alpaca': {
            'api_key': 'test_key',
            'secret_key': 'test_secret',
            'paper_trading': True
        }
    })
    
    order_service = test_container.order_service()
    # Test with paper trading account
```

## Rollback Plan

If issues arise, the old code is preserved and can be restored:

1. **Revert imports**: Use the migration script in reverse
2. **Restore old modules**: Old files are backed up with `.old` extension
3. **Update configuration**: Switch back to old dependency injection
4. **Test thoroughly**: Ensure all functionality works as before

## Next Steps

1. **Run migration script**: Execute the automated import migration
2. **Update tests**: Modify tests to use new architecture
3. **Performance testing**: Validate that performance is maintained
4. **Documentation**: Update all documentation to reflect new architecture
5. **Team training**: Train team on new patterns and practices
'''

    path = Path("MIGRATION_DOCUMENTATION.md")
    path.write_text(migration_doc_content)

    print("✅ Created migration documentation")


def main():
    """Execute the migration."""
    print("🚀 Starting Alpaca Architecture Migration...")
    print()

    try:
        create_directory_structure()
        create_infrastructure_adapters()
        create_domain_interfaces()
        create_domain_models()
        create_service_layer()
        create_dependency_injection()
        create_migration_documentation()

        print()
        print("✅ Migration Phase 1 Complete!")
        print()
        print("Next steps:")
        print("1. Install dependency-injector: pip install dependency-injector")
        print("2. Review the generated code in the new directories")
        print("3. Run tests to ensure everything works")
        print("4. Begin migrating existing code to use the new services")
        print("5. Read MIGRATION_DOCUMENTATION.md for detailed guidance")
        print()
        print("The new architecture provides:")
        print("- Clean separation of concerns")
        print("- Easy testing with mock repositories")
        print("- Type safety throughout the stack")
        print("- Centralized dependency management")
        print("- Extensibility for future brokers/data sources")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
