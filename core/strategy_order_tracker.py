#!/usr/bin/env python3
"""
Strategy Order Tracking System

This module tracks Alpaca orders and positions by strategy to enable proper
position attribution and management across multiple strategies.

Features:
- Maps Alpaca order IDs to strategies
- Tracks position origins (which strategy created them)
- Enables strategy-specific position management
- Persistent storage of order/position mappings
- Historical order tracking for analysis
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum

from core.config import Config
from core.strategy_manager import StrategyType


@dataclass
class StrategyOrder:
    """Represents an order placed by a specific strategy"""
    order_id: str
    strategy_type: str  # StrategyType enum value
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: Optional[float]
    status: str  # submitted, filled, canceled, etc.
    timestamp: str
    reason: str  # Strategy reason for the order
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyOrder':
        return cls(**data)


@dataclass
class StrategyPosition:
    """Represents a position owned by a specific strategy"""
    symbol: str
    strategy_type: str
    quantity: float
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    created_timestamp: str
    last_updated: str
    contributing_orders: List[str]  # Order IDs that built this position
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyPosition':
        return cls(**data)


class StrategyOrderTracker:
    """Tracks orders and positions by strategy"""
    
    def __init__(self):
        self.config = Config()
        
        # Storage files
        self.orders_file = self.config['logging'].get(
            'strategy_orders', 
            '/tmp/strategy_orders.json'
        )
        self.positions_file = self.config['logging'].get(
            'strategy_positions_detailed', 
            '/tmp/strategy_positions_detailed.json'
        )
        
        # Ensure directories exist
        for file_path in [self.orders_file, self.positions_file]:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        logging.info(f"StrategyOrderTracker initialized with files: {self.orders_file}, {self.positions_file}")
    
    def record_order(self, order_id: str, strategy_type: StrategyType, symbol: str, 
                    side: str, quantity: float, price: Optional[float], 
                    reason: str) -> None:
        """Record a new order placed by a strategy"""
        try:
            order = StrategyOrder(
                order_id=order_id,
                strategy_type=strategy_type.value,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                status="submitted",
                timestamp=datetime.now().isoformat(),
                reason=reason
            )
            
            # Load existing orders
            orders = self._load_orders()
            
            # Add new order
            orders[order_id] = order.to_dict()
            
            # Save updated orders
            self._save_orders(orders)
            
            logging.info(f"Recorded order {order_id} for {strategy_type.value}: {side} {quantity} {symbol}")
            
        except Exception as e:
            logging.error(f"Error recording order {order_id}: {e}")
    
    def update_order_status(self, order_id: str, status: str) -> None:
        """Update the status of an existing order"""
        try:
            orders = self._load_orders()
            
            if order_id in orders:
                orders[order_id]['status'] = status
                orders[order_id]['last_updated'] = datetime.now().isoformat()
                self._save_orders(orders)
                logging.info(f"Updated order {order_id} status to {status}")
            else:
                logging.warning(f"Order {order_id} not found for status update")
                
        except Exception as e:
            logging.error(f"Error updating order status for {order_id}: {e}")
    
    def get_strategy_orders(self, strategy_type: StrategyType, 
                           days_back: int = 30) -> List[StrategyOrder]:
        """Get all orders for a specific strategy within time window"""
        try:
            orders = self._load_orders()
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            strategy_orders = []
            for order_data in orders.values():
                if order_data['strategy_type'] == strategy_type.value:
                    order_time = datetime.fromisoformat(order_data['timestamp'])
                    if order_time >= cutoff_date:
                        strategy_orders.append(StrategyOrder.from_dict(order_data))
            
            return strategy_orders
            
        except Exception as e:
            logging.error(f"Error getting strategy orders: {e}")
            return []
    
    def reconcile_positions_with_alpaca(self, alpaca_positions: Dict[str, Any]) -> Dict[str, List[StrategyPosition]]:
        """
        Reconcile current Alpaca positions with strategy tracking
        
        Args:
            alpaca_positions: Dict from AlpacaTradingBot.get_positions()
            
        Returns:
            Dict mapping strategy names to their positions
        """
        try:
            # Load existing strategy positions
            strategy_positions = self._load_positions()
            
            # Load orders to determine position origins
            orders = self._load_orders()
            
            # Group orders by symbol and strategy
            symbol_strategy_orders = {}
            for order_data in orders.values():
                if order_data['status'] == 'filled':
                    symbol = order_data['symbol']
                    strategy = order_data['strategy_type']
                    key = f"{symbol}_{strategy}"
                    
                    if key not in symbol_strategy_orders:
                        symbol_strategy_orders[key] = []
                    symbol_strategy_orders[key].append(order_data)
            
            # Update strategy positions based on current Alpaca positions
            updated_positions = {strategy.value: [] for strategy in StrategyType}
            
            for symbol, alpaca_pos in alpaca_positions.items():
                current_qty = alpaca_pos.get('qty', 0)
                
                if current_qty == 0:
                    continue  # Skip zero positions
                
                # Determine which strategies contributed to this position
                contributing_strategies = []
                for strategy in StrategyType:
                    key = f"{symbol}_{strategy.value}"
                    if key in symbol_strategy_orders:
                        contributing_strategies.append(strategy)
                
                if not contributing_strategies:
                    # Position exists but no tracked orders - could be manual or legacy
                    logging.warning(f"Position {symbol} ({current_qty}) has no tracked strategy orders")
                    continue
                
                # Allocate position proportionally to contributing strategies
                total_contributed_qty = 0
                strategy_contributions = {}
                
                for strategy in contributing_strategies:
                    key = f"{symbol}_{strategy.value}"
                    net_qty = 0
                    
                    for order_data in symbol_strategy_orders[key]:
                        qty = order_data['quantity']
                        if order_data['side'] == 'BUY':
                            net_qty += qty
                        else:  # SELL
                            net_qty -= qty
                    
                    if net_qty > 0:
                        strategy_contributions[strategy] = net_qty
                        total_contributed_qty += net_qty
                
                # Allocate current position proportionally
                if total_contributed_qty > 0:
                    for strategy, contributed_qty in strategy_contributions.items():
                        allocation_ratio = contributed_qty / total_contributed_qty
                        allocated_qty = current_qty * allocation_ratio
                        
                        if allocated_qty > 0.001:  # Minimum threshold
                            strategy_pos = StrategyPosition(
                                symbol=symbol,
                                strategy_type=strategy.value,
                                quantity=allocated_qty,
                                avg_cost=alpaca_pos.get('cost_basis', 0) / alpaca_pos.get('qty', 1),
                                market_value=alpaca_pos.get('market_value', 0) * allocation_ratio,
                                unrealized_pnl=alpaca_pos.get('unrealized_pl', 0) * allocation_ratio,
                                created_timestamp=datetime.now().isoformat(),
                                last_updated=datetime.now().isoformat(),
                                contributing_orders=[
                                    order_data['order_id'] 
                                    for order_data in symbol_strategy_orders.get(f"{symbol}_{strategy.value}", [])
                                ]
                            )
                            updated_positions[strategy.value].append(strategy_pos)
            
            # Save updated positions
            self._save_positions(updated_positions)
            
            return updated_positions
            
        except Exception as e:
            logging.error(f"Error reconciling positions: {e}")
            return {strategy.value: [] for strategy in StrategyType}
    
    def get_strategy_attribution(self) -> Dict[str, Dict[str, float]]:
        """
        Get portfolio attribution by strategy
        
        Returns:
            Dict mapping strategy names to their portfolio statistics
        """
        try:
            positions = self._load_positions()
            attribution = {}
            
            for strategy_name, strategy_positions in positions.items():
                total_value = sum(pos['market_value'] for pos in strategy_positions)
                total_pnl = sum(pos['unrealized_pnl'] for pos in strategy_positions)
                position_count = len(strategy_positions)
                
                attribution[strategy_name] = {
                    'total_value': total_value,
                    'unrealized_pnl': total_pnl,
                    'position_count': position_count,
                    'symbols': [pos['symbol'] for pos in strategy_positions]
                }
            
            return attribution
            
        except Exception as e:
            logging.error(f"Error getting strategy attribution: {e}")
            return {}
    
    def cleanup_old_orders(self, days_to_keep: int = 90) -> int:
        """Remove old orders to prevent file bloat"""
        try:
            orders = self._load_orders()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            orders_to_remove = []
            for order_id, order_data in orders.items():
                order_time = datetime.fromisoformat(order_data['timestamp'])
                if order_time < cutoff_date:
                    orders_to_remove.append(order_id)
            
            for order_id in orders_to_remove:
                del orders[order_id]
            
            self._save_orders(orders)
            
            logging.info(f"Cleaned up {len(orders_to_remove)} old orders")
            return len(orders_to_remove)
            
        except Exception as e:
            logging.error(f"Error cleaning up orders: {e}")
            return 0
    
    def _load_orders(self) -> Dict[str, Dict]:
        """Load orders from storage"""
        try:
            if not os.path.exists(self.orders_file):
                return {}
            
            with open(self.orders_file, 'r') as f:
                data = json.load(f)
                return data.get('orders', {})
        except Exception as e:
            logging.error(f"Error loading orders: {e}")
            return {}
    
    def _save_orders(self, orders: Dict[str, Dict]) -> None:
        """Save orders to storage"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'orders': orders
            }
            
            with open(self.orders_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving orders: {e}")
    
    def _load_positions(self) -> Dict[str, List[Dict]]:
        """Load positions from storage"""
        try:
            if not os.path.exists(self.positions_file):
                return {strategy.value: [] for strategy in StrategyType}
            
            with open(self.positions_file, 'r') as f:
                data = json.load(f)
                return data.get('positions', {strategy.value: [] for strategy in StrategyType})
        except Exception as e:
            logging.error(f"Error loading positions: {e}")
            return {strategy.value: [] for strategy in StrategyType}
    
    def _save_positions(self, positions: Dict[str, List]) -> None:
        """Save positions to storage"""
        try:
            # Convert StrategyPosition objects to dicts if needed
            serializable_positions = {}
            for strategy, pos_list in positions.items():
                serializable_positions[strategy] = []
                for pos in pos_list:
                    if isinstance(pos, StrategyPosition):
                        serializable_positions[strategy].append(pos.to_dict())
                    else:
                        serializable_positions[strategy].append(pos)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'positions': serializable_positions
            }
            
            with open(self.positions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving positions: {e}")


def main():
    """Test the strategy order tracker"""
    import pprint
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Strategy Order Tracker")
    print("=" * 40)
    
    tracker = StrategyOrderTracker()
    
    # Test recording orders
    print("📝 Recording test orders...")
    tracker.record_order("test-001", StrategyType.NUCLEAR, "SMR", "BUY", 100, 15.50, "Nuclear bull signal")
    tracker.record_order("test-002", StrategyType.TECL, "TECL", "BUY", 50, 45.20, "TECL strategy signal")
    
    # Test order status updates
    print("🔄 Updating order statuses...")
    tracker.update_order_status("test-001", "filled")
    tracker.update_order_status("test-002", "filled")
    
    # Test getting strategy orders
    print("📊 Getting Nuclear strategy orders...")
    nuclear_orders = tracker.get_strategy_orders(StrategyType.NUCLEAR)
    print(f"Found {len(nuclear_orders)} Nuclear orders")
    
    # Test position reconciliation (mock data)
    print("🏦 Testing position reconciliation...")
    mock_alpaca_positions = {
        "SMR": {
            "qty": 100,
            "market_value": 1600,
            "cost_basis": 1550,
            "unrealized_pl": 50,
        },
        "TECL": {
            "qty": 50,
            "market_value": 2400,
            "cost_basis": 2260,
            "unrealized_pl": 140,
        }
    }
    
    strategy_positions = tracker.reconcile_positions_with_alpaca(mock_alpaca_positions)
    print("Strategy positions:")
    pprint.pprint(strategy_positions)
    
    # Test attribution
    print("📈 Getting strategy attribution...")
    attribution = tracker.get_strategy_attribution()
    pprint.pprint(attribution)
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    main()
