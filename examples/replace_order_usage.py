"""Business Unit: shared | Status: current.

Integration example showing replace order usage.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from alpaca.trading.requests import ReplaceOrderRequest

if TYPE_CHECKING:
    from alpaca.trading.models import Order

    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager


def example_replace_order_usage() -> tuple[Callable[..., Order | dict[str, object] | None], Callable[..., Order | dict[str, object] | None], Callable[..., Order | dict[str, object] | None]]:
    """Demonstrate how to use the new replace order functionality."""
    
    # Example 1: Replace order with new quantity
    def replace_order_quantity(alpaca_manager: AlpacaManager, order_id: str, new_quantity: int) -> Order | dict[str, object] | None:
        """Replace an order with a new quantity."""
        replace_request = ReplaceOrderRequest(qty=new_quantity)
        result = alpaca_manager.replace_order(order_id, replace_request)
        
        if result is not None:
            print(f"Order {order_id} successfully replaced with new quantity: {new_quantity}")
            return result
        print(f"Failed to replace order {order_id}")
        return None
    
    # Example 2: Replace order with new limit price
    def replace_order_limit_price(alpaca_manager: AlpacaManager, order_id: str, new_limit_price: float) -> Order | dict[str, object] | None:
        """Replace an order with a new limit price."""
        replace_request = ReplaceOrderRequest(limit_price=new_limit_price)
        result = alpaca_manager.replace_order(order_id, replace_request)
        
        if result is not None:
            print(f"Order {order_id} successfully replaced with new limit price: ${new_limit_price}")
            return result
        print(f"Failed to replace order {order_id}")
        return None
    
    # Example 3: Replace order with multiple parameters
    def replace_order_multiple_params(alpaca_manager: AlpacaManager, order_id: str, new_qty: int, new_limit_price: float) -> Order | dict[str, object] | None:
        """Replace an order with multiple new parameters."""
        replace_request = ReplaceOrderRequest(
            qty=new_qty,
            limit_price=new_limit_price,
            time_in_force="gtc"  # Good till cancelled
        )
        result = alpaca_manager.replace_order(order_id, replace_request)
        
        if result is not None:
            print(f"Order {order_id} successfully replaced with qty: {new_qty}, limit: ${new_limit_price}")
            return result
        print(f"Failed to replace order {order_id}")
        return None
    
    # Examples usage would be:
    # alpaca_manager = AlpacaManager(api_key="your_key", secret_key="your_secret", paper=True)
    # 
    # # Get an existing order ID
    # orders = alpaca_manager.get_orders(status="open")
    # if orders:
    #     order_id = orders[0].id
    #     
    #     # Replace just the quantity
    #     replace_order_quantity(alpaca_manager, order_id, 100)
    #     
    #     # Replace just the limit price
    #     replace_order_limit_price(alpaca_manager, order_id, 150.50)
    #     
    #     # Replace multiple parameters
    #     replace_order_multiple_params(alpaca_manager, order_id, 50, 155.00)
    
    return replace_order_quantity, replace_order_limit_price, replace_order_multiple_params


if __name__ == "__main__":
    # This is just an example module - run tests instead for actual validation
    print("Replace order functionality examples defined.")
    print("See tests/shared/services/test_alpaca_trading_service.py for actual tests.")