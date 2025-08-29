"""Business Unit: strategy & signal generation | Status: current

Use case for generating strategy signals from market data.
"""

from typing import Sequence
from decimal import Decimal
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.application.ports import MarketDataPort, SignalPublisherPort
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1
from the_alchemiser.strategy.domain.value_objects.market_bar_vo import MarketBarVO


class GenerateSignalsUseCase:
    """Orchestrates signal generation and publication."""
    
    def __init__(
        self,
        market_data: MarketDataPort,
        signal_publisher: SignalPublisherPort,
    ) -> None:
        self._market_data = market_data
        self._signal_publisher = signal_publisher
    
    def execute(self, symbols: Sequence[Symbol]) -> Sequence[SignalContractV1]:
        """Generate and publish signals for given symbols.
        
        Args:
            symbols: Sequence of symbols to analyze
            
        Returns:
            Sequence of published signal contracts
            
        Raises:
            DataAccessError: Market data failure
            SymbolNotFoundError: Invalid symbol
            PublishError: Signal publishing failure
        """
        signals = []
        
        for symbol in symbols:
            # Fetch market data via port
            latest_bar = self._market_data.get_latest_bar(symbol, "1Day")
            history = self._market_data.get_history(symbol, "1Day", 50)
            
            # Simple signal generation example (normally would use domain service)
            # This is a simplified example - real logic would be in domain layer
            signal_strength = self._calculate_simple_signal(latest_bar, history)
            
            if abs(signal_strength) > 0.5:  # Threshold for signal
                signal_contract = self._create_signal_contract(symbol, signal_strength)
                self._signal_publisher.publish(signal_contract)
                signals.append(signal_contract)
        
        return signals
    
    def _calculate_simple_signal(self, latest_bar: MarketBarVO, history: Sequence[MarketBarVO]) -> float:
        """Simple signal calculation (example only)."""
        # This is a placeholder - real signal logic would be in domain
        # Just return a simple momentum-based signal
        if len(history) < 20:
            return 0.0
        
        recent_prices = [bar.close_price for bar in history[-10:]]
        older_prices = [bar.close_price for bar in history[-20:-10]]
        
        recent_avg = sum(recent_prices) / Decimal('10')
        older_avg = sum(older_prices) / Decimal('10')
        
        if older_avg == Decimal('0'):
            return 0.0
        
        return float((recent_avg - older_avg) / older_avg)
    
    def _create_signal_contract(self, symbol: Symbol, strength: float) -> SignalContractV1:
        """Create signal contract from calculation results."""
        # This would normally use a domain service or factory
        # Simplified example for demonstration
        from uuid import uuid4
        from decimal import Decimal
        from the_alchemiser.shared_kernel import ActionType
        from the_alchemiser.shared_kernel.value_objects.percentage import Percentage
        
        action = ActionType.BUY if strength > 0 else ActionType.SELL
        
        return SignalContractV1(
            correlation_id=uuid4(),
            symbol=symbol,
            action=action,
            target_allocation=Percentage(Decimal(str(abs(strength) * 0.1))),  # 10% max
            confidence=abs(strength),
            reasoning=f"Simple momentum signal: {strength:.3f}"
        )