#!/usr/bin/env python3
"""
Strategy Order Tracker for Per-Strategy P&L Management

This module provides dedicated tracking of orders by strategy for accurate P&L calculations.
It persists order data to S3 for durability and calculates realized/unrealized P&L per strategy.

Key Features:
- Tag orders with strategy information during execution
- Maintain positions and average cost on a per-strategy basis
- Calculate realized P&L when positions are reduced/closed
- Calculate unrealized P&L from current market prices
- Persist order history to S3 for long-term tracking
- Support for both individual strategy and portfolio-wide P&L

Design:
- Uses existing S3 utilities for persistent storage
- Integrates with trading engine to capture order fills
- Provides P&L metrics for email reporting and dashboards
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from the_alchemiser.core.trading.strategy_manager import StrategyType
from the_alchemiser.core.utils.s3_utils import get_s3_handler
from the_alchemiser.core.config import get_config


@dataclass
class StrategyOrder:
    """Represents a completed order tagged with strategy information."""
    order_id: str
    strategy: str  # StrategyType.value
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    timestamp: str  # ISO format
    
    @classmethod
    def from_order_data(cls, order_id: str, strategy: StrategyType, symbol: str, 
                       side: str, quantity: float, price: float) -> 'StrategyOrder':
        """Create StrategyOrder from order execution data."""
        return cls(
            order_id=order_id,
            strategy=strategy.value,
            symbol=symbol,
            side=side.upper(),
            quantity=float(quantity),
            price=float(price),
            timestamp=datetime.now(timezone.utc).isoformat()
        )


@dataclass
class StrategyPosition:
    """Represents a position held by a specific strategy."""
    strategy: str
    symbol: str
    quantity: float
    average_cost: float
    total_cost: float
    last_updated: str
    
    def update_with_order(self, order: StrategyOrder) -> None:
        """Update position with new order data."""
        if order.side == 'BUY':
            # Add to position
            new_total_cost = self.total_cost + (order.quantity * order.price)
            new_quantity = self.quantity + order.quantity
            if new_quantity > 0:
                self.average_cost = new_total_cost / new_quantity
            self.quantity = new_quantity
            self.total_cost = new_total_cost
        elif order.side == 'SELL':
            # Reduce position
            if self.quantity <= 0:
                logging.warning(f"Attempted to sell {order.symbol} with no position in {order.strategy}")
                return
            
            # Use FIFO accounting for cost basis
            self.quantity -= order.quantity
            if self.quantity <= 0:
                # Position closed
                self.quantity = 0
                self.total_cost = 0
                self.average_cost = 0
            else:
                # Reduce total cost proportionally
                self.total_cost = self.quantity * self.average_cost
        
        self.last_updated = order.timestamp


@dataclass
class StrategyPnL:
    """P&L metrics for a specific strategy."""
    strategy: str
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    positions: Dict[str, float]  # symbol -> quantity
    allocation_value: float
    
    @property
    def total_return_pct(self) -> float:
        """Calculate total return percentage."""
        if self.allocation_value <= 0:
            return 0.0
        return (self.total_pnl / self.allocation_value) * 100


class StrategyOrderTracker:
    """Dedicated component for tracking orders and P&L by strategy."""
    
    def __init__(self, config=None):
        """Initialize tracker with S3 configuration."""
        self.config = config or get_config()
        self.s3_handler = get_s3_handler()
        
        # S3 paths for data persistence
        tracking_config = self.config.get('tracking') if self.config else {}
        if not tracking_config:
            tracking_config = {}
        
        bucket = tracking_config.get('s3_bucket', 'the-alchemiser-s3')
        
        self.orders_s3_path = f"s3://{bucket}/{tracking_config.get('strategy_orders_path', 'strategy_orders/')}"
        self.positions_s3_path = f"s3://{bucket}/{tracking_config.get('strategy_positions_path', 'strategy_positions/')}"
        self.pnl_history_s3_path = f"s3://{bucket}/{tracking_config.get('strategy_pnl_history_path', 'strategy_pnl_history/')}"
        self.order_history_limit = int(tracking_config.get('order_history_limit', 1000))
        
        # In-memory caches
        self._orders_cache: List[StrategyOrder] = []
        self._positions_cache: Dict[Tuple[str, str], StrategyPosition] = {}  # (strategy, symbol) -> position
        self._realized_pnl_cache: Dict[str, float] = {}  # strategy -> realized P&L
        
        # Load existing data
        self._load_data()
        
        logging.info("StrategyOrderTracker initialized with S3 persistence")
    
    def record_order(self, order_id: str, strategy: StrategyType, symbol: str,
                    side: str, quantity: float, price: float) -> None:
        """Record a completed order with strategy tagging."""
        try:
            # Create order record
            order = StrategyOrder.from_order_data(
                order_id, strategy, symbol, side, quantity, price
            )
            
            # Add to cache
            self._orders_cache.append(order)
            
            # Update position
            self._update_position(order)
            
            # Calculate realized P&L if this is a sell
            if side.upper() == 'SELL':
                self._calculate_realized_pnl(order)
            
            # Persist to S3
            self._persist_order(order)
            self._persist_positions()
            
            logging.info(f"Recorded {strategy.value} order: {side} {quantity} {symbol} @ ${price:.2f}")
            
        except Exception as e:
            logging.error(f"Failed to record order {order_id}: {e}")
    
    def get_strategy_pnl(self, strategy: StrategyType, current_prices: Optional[Dict[str, float]] = None) -> StrategyPnL:
        """Calculate comprehensive P&L for a strategy."""
        strategy_str = strategy.value
        
        # Get positions for this strategy
        strategy_positions = {
            symbol: pos.quantity 
            for (strat, symbol), pos in self._positions_cache.items() 
            if strat == strategy_str and pos.quantity > 0
        }
        
        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        allocation_value = 0.0
        
        if current_prices:
            for symbol, quantity in strategy_positions.items():
                if symbol in current_prices and quantity > 0:
                    position = self._positions_cache.get((strategy_str, symbol))
                    if position:
                        current_value = quantity * current_prices[symbol]
                        cost_basis = quantity * position.average_cost
                        unrealized_pnl += (current_value - cost_basis)
                        allocation_value += current_value
        
        # Get realized P&L
        realized_pnl = self._realized_pnl_cache.get(strategy_str, 0.0)
        
        # Calculate total P&L
        total_pnl = realized_pnl + unrealized_pnl
        
        return StrategyPnL(
            strategy=strategy_str,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            positions=strategy_positions,
            allocation_value=allocation_value
        )
    
    def get_all_strategy_pnl(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[StrategyType, StrategyPnL]:
        """Get P&L for all strategies."""
        result = {}
        for strategy in StrategyType:
            result[strategy] = self.get_strategy_pnl(strategy, current_prices)
        return result
    
    def get_order_history(self, strategy: Optional[StrategyType] = None,
                         symbol: Optional[str] = None, days: int = 30) -> List[StrategyOrder]:
        """Get filtered order history."""
        # Filter by strategy
        orders = self._orders_cache
        if strategy:
            orders = [o for o in orders if o.strategy == strategy.value]
        
        # Filter by symbol
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        # Filter by date (last N days)
        if days > 0:
            cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            cutoff_str = cutoff_date.isoformat()
            orders = [o for o in orders if o.timestamp >= cutoff_str]
        
        # Sort by timestamp (most recent first)
        orders.sort(key=lambda x: x.timestamp, reverse=True)
        return orders
    
    def archive_daily_pnl(self, current_prices: Optional[Dict[str, float]] = None) -> None:
        """Archive daily P&L snapshot for historical tracking."""
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            # Get P&L for all strategies
            all_pnl = self.get_all_strategy_pnl(current_prices)
            
            # Create archive record
            archive_data = {
                'date': today,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'strategies': {
                    strategy.value: asdict(pnl) for strategy, pnl in all_pnl.items()
                }
            }
            
            # Save to S3
            archive_path = f"{self.pnl_history_s3_path}{today}.json"
            success = self.s3_handler.write_json(archive_path, archive_data)
            
            if success:
                logging.info(f"Archived daily P&L snapshot for {today}")
            else:
                logging.error(f"Failed to archive daily P&L for {today}")
                
        except Exception as e:
            logging.error(f"Error archiving daily P&L: {e}")
    
    def _update_position(self, order: StrategyOrder) -> None:
        """Update position cache with new order."""
        key = (order.strategy, order.symbol)
        
        if key not in self._positions_cache:
            # Create new position
            self._positions_cache[key] = StrategyPosition(
                strategy=order.strategy,
                symbol=order.symbol,
                quantity=0.0,
                average_cost=0.0,
                total_cost=0.0,
                last_updated=order.timestamp
            )
        
        # Update existing position
        self._positions_cache[key].update_with_order(order)
    
    def _calculate_realized_pnl(self, sell_order: StrategyOrder) -> None:
        """Calculate realized P&L from a sell order."""
        try:
            key = (sell_order.strategy, sell_order.symbol)
            position = self._positions_cache.get(key)
            
            if not position or position.average_cost <= 0:
                logging.warning(f"No position data for realized P&L calculation: {sell_order.symbol}")
                return
            
            # Calculate realized P&L for this sale
            cost_basis = sell_order.quantity * position.average_cost
            sale_proceeds = sell_order.quantity * sell_order.price
            realized_pnl = sale_proceeds - cost_basis
            
            # Add to strategy's total realized P&L
            if sell_order.strategy not in self._realized_pnl_cache:
                self._realized_pnl_cache[sell_order.strategy] = 0.0
            
            self._realized_pnl_cache[sell_order.strategy] += realized_pnl
            
            logging.info(f"Realized P&L for {sell_order.strategy} {sell_order.symbol}: ${realized_pnl:.2f}")
            
        except Exception as e:
            logging.error(f"Error calculating realized P&L: {e}")
    
    def _load_data(self) -> None:
        """Load existing data from S3."""
        try:
            # Load orders (last 90 days to limit memory usage)
            self._load_recent_orders(days=90)
            
            # Load positions
            self._load_positions()
            
            # Load realized P&L
            self._load_realized_pnl()
            
        except Exception as e:
            logging.error(f"Error loading tracker data: {e}")
    
    def _load_recent_orders(self, days: int = 90) -> None:
        """Load recent orders from S3."""
        try:
            # For now, load from a consolidated orders file
            # In production, you might want to partition by date
            orders_path = f"{self.orders_s3_path}recent_orders.json"
            
            if self.s3_handler.file_exists(orders_path):
                data = self.s3_handler.read_json(orders_path)
                if data and 'orders' in data:
                    for order_data in data['orders']:
                        order = StrategyOrder(**order_data)
                        self._orders_cache.append(order)
                    
                    # Filter to last N days
                    cutoff_date = datetime.now(timezone.utc).replace(day=datetime.now().day - days)
                    cutoff_str = cutoff_date.isoformat()
                    self._orders_cache = [o for o in self._orders_cache if o.timestamp >= cutoff_str]
                    
                    logging.info(f"Loaded {len(self._orders_cache)} recent orders")
        except Exception as e:
            logging.error(f"Error loading orders: {e}")
    
    def _load_positions(self) -> None:
        """Load current positions from S3."""
        try:
            positions_path = f"{self.positions_s3_path}current_positions.json"
            
            if self.s3_handler.file_exists(positions_path):
                data = self.s3_handler.read_json(positions_path)
                if data and 'positions' in data:
                    for pos_data in data['positions']:
                        pos = StrategyPosition(**pos_data)
                        key = (pos.strategy, pos.symbol)
                        self._positions_cache[key] = pos
                    
                    logging.info(f"Loaded {len(self._positions_cache)} positions")
        except Exception as e:
            logging.error(f"Error loading positions: {e}")
    
    def _load_realized_pnl(self) -> None:
        """Load realized P&L from S3."""
        try:
            pnl_path = f"{self.positions_s3_path}realized_pnl.json"
            
            if self.s3_handler.file_exists(pnl_path):
                data = self.s3_handler.read_json(pnl_path)
                if data:
                    self._realized_pnl_cache = data
                    logging.info(f"Loaded realized P&L for {len(data)} strategies")
        except Exception as e:
            logging.error(f"Error loading realized P&L: {e}")
    
    def _persist_order(self, order: StrategyOrder) -> None:
        """Persist single order to S3."""
        try:
            # Add to recent orders file
            orders_path = f"{self.orders_s3_path}recent_orders.json"
            
            # Load existing data
            existing_data = self.s3_handler.read_json(orders_path) or {'orders': []}
            
            # Add new order
            existing_data['orders'].append(asdict(order))
            
            # Keep only last N orders to limit file size
            if len(existing_data['orders']) > self.order_history_limit:
                existing_data['orders'] = existing_data['orders'][-self.order_history_limit:]
            
            # Save back
            self.s3_handler.write_json(orders_path, existing_data)
            
        except Exception as e:
            logging.error(f"Error persisting order: {e}")
    
    def _persist_positions(self) -> None:
        """Persist all positions to S3."""
        try:
            positions_data = {
                'positions': [asdict(pos) for pos in self._positions_cache.values()],
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            positions_path = f"{self.positions_s3_path}current_positions.json"
            self.s3_handler.write_json(positions_path, positions_data)
            
            # Also save realized P&L
            pnl_path = f"{self.positions_s3_path}realized_pnl.json"
            self.s3_handler.write_json(pnl_path, self._realized_pnl_cache)
            
        except Exception as e:
            logging.error(f"Error persisting positions: {e}")
    
    def get_summary_for_email(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get summary data suitable for email reporting."""
        try:
            all_pnl = self.get_all_strategy_pnl(current_prices)
            
            summary = {
                'total_portfolio_pnl': sum(pnl.total_pnl for pnl in all_pnl.values()),
                'total_realized_pnl': sum(pnl.realized_pnl for pnl in all_pnl.values()),
                'total_unrealized_pnl': sum(pnl.unrealized_pnl for pnl in all_pnl.values()),
                'strategies': {}
            }
            
            for strategy, pnl in all_pnl.items():
                summary['strategies'][strategy.value] = {
                    'realized_pnl': pnl.realized_pnl,
                    'unrealized_pnl': pnl.unrealized_pnl,
                    'total_pnl': pnl.total_pnl,
                    'total_return_pct': pnl.total_return_pct,
                    'allocation_value': pnl.allocation_value,
                    'position_count': len([q for q in pnl.positions.values() if q > 0])
                }
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating email summary: {e}")
            return {}


# Global instance for easy access
_strategy_tracker = None

def get_strategy_tracker() -> StrategyOrderTracker:
    """Get or create global strategy order tracker instance."""
    global _strategy_tracker
    if _strategy_tracker is None:
        _strategy_tracker = StrategyOrderTracker()
    return _strategy_tracker
