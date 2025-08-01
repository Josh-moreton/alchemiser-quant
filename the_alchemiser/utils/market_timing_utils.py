#!/usr/bin/env python3
"""
Market Open Timing Utilities

Implements the timing logic from better orders spec for optimal execution
during market open hours (9:30-9:35 ET).
"""

from datetime import datetime, time
from enum import Enum
from typing import Tuple, Optional
import pytz

class ExecutionStrategy(Enum):
    WAIT_FOR_SPREADS = "wait_for_spreads"    # 9:30-9:32 with wide spreads
    NORMAL_EXECUTION = "normal_execution"     # 9:32-9:35
    STANDARD_EXECUTION = "standard_execution" # After 9:35

class MarketOpenTimingEngine:
    """Market open timing decisions per better orders specification."""
    
    def __init__(self):
        self.et_tz = pytz.timezone('US/Eastern')
        
    def get_execution_strategy(self, current_time: Optional[datetime] = None) -> ExecutionStrategy:
        """Determine execution strategy based on market timing."""
        if current_time is None:
            current_time = datetime.now(self.et_tz)
        
        # Convert to ET time
        et_time = current_time.astimezone(self.et_tz).time()
        
        market_open = time(9, 30)   # 9:30 ET
        spreads_normalize = time(9, 32)  # 9:32 ET  
        market_stable = time(9, 35)     # 9:35 ET
        
        if market_open <= et_time < spreads_normalize:
            return ExecutionStrategy.WAIT_FOR_SPREADS
        elif spreads_normalize <= et_time < market_stable:
            return ExecutionStrategy.NORMAL_EXECUTION
        else:
            return ExecutionStrategy.STANDARD_EXECUTION
    
    def should_execute_immediately(self, spread_cents: float, strategy: ExecutionStrategy) -> bool:
        """Apply spread-based execution decisions."""
        if strategy == ExecutionStrategy.STANDARD_EXECUTION:
            return True  # Always execute after 9:35
        
        # Market open logic
        if spread_cents <= 3.0:  # Tight spread
            return True
        elif spread_cents > 5.0:  # Wide spread
            return strategy != ExecutionStrategy.WAIT_FOR_SPREADS
        else:  # Normal spread
            return True
            
    def get_wait_time_seconds(self, strategy: ExecutionStrategy, spread_cents: float) -> int:
        """Get recommended wait time before execution."""
        if strategy == ExecutionStrategy.WAIT_FOR_SPREADS and spread_cents > 5.0:
            return 90  # Wait 1.5 minutes for spreads to normalize
        return 0
