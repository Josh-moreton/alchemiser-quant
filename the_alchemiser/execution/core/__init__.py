"""Business Unit: execution | Status: current.

Core execution engine and execution management.
"""

from __future__ import annotations

from .account_management_service import AccountManagementService
from .data_transformation_service import DataTransformationService
from .execution_schemas import *
from .lifecycle_coordinator import LifecycleCoordinator
from .order_execution_service import OrderExecutionService
from .refactored_execution_manager import RefactoredTradingServiceManager

# Provide backward compatibility alias
TradingServiceManager = RefactoredTradingServiceManager

__all__ = [
    "AccountManagementService",
    "DataTransformationService",
    "LifecycleCoordinator",
    "OrderExecutionService",
    "RefactoredTradingServiceManager",
    "TradingServiceManager",
]
