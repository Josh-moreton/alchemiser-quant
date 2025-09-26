"""Business Unit: shared | Status: current.

DEPRECATED: This module has been modularized into shared.services.pricing package.

This module now serves as a compatibility shim that imports from the new
modular package structure. The monolithic implementation has been split into
focused modules for better maintainability and testability.

New imports should use:
    from the_alchemiser.shared.services.pricing import RealTimePricingService

Migration guide:
- RealTimePricingService: No changes to public API
- RealTimeQuote: Available from the new package
- All public methods work identically

The new package structure:
- facade.py: Main service implementation
- models.py: Data structures and DTOs
- quote_parser.py / trade_parser.py: Data parsing utilities
- subscription_planner.py: Subscription management logic
- data_store.py: Thread-safe data storage
- stream_runner.py: Stream lifecycle management
- stats.py: Metrics collection
- cleanup.py: Memory management
- bootstrap.py: Configuration loading
- compat.py: Legacy compatibility helpers
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "shared.services.real_time_pricing is deprecated. "
    "Use 'from the_alchemiser.shared.services.pricing import RealTimePricingService' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# ruff: noqa: F403, E402
# Import everything from the new package for backward compatibility
from the_alchemiser.shared.services.pricing import *

# Re-export the main classes for compatibility  
from the_alchemiser.shared.services.pricing import RealTimePricingService, RealTimeQuote

__all__ = ["RealTimePricingService", "RealTimeQuote"]