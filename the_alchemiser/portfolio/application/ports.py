"""Business Unit: portfolio assessment & management | Status: current

Port protocols for Portfolio context external dependencies.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
)
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    RebalancePlanContractV1,
)
from the_alchemiser.portfolio.domain.entities.position import Position
from the_alchemiser.portfolio.domain.value_objects.portfolio_snapshot_vo import PortfolioSnapshotVO
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol


class PositionRepositoryPort(Protocol):
    """Port for persisting and retrieving portfolio position state.
    
    Responsibilities:
    - Load current position holdings
    - Persist position updates atomically
    - Handle position lookup by symbol
    
    NOT responsible for:
    - Position valuation (belongs in domain)
    - Risk calculations (belongs in domain)
    - Order generation (belongs in application)
    
    Error expectations:
    - Raises DataAccessError for storage failures
    - Raises ConcurrencyError for optimistic locking violations
    
    Idempotency: save_positions with same data has no additional effect
    """
    
    def load_positions(self) -> Sequence[Position]:
        """Load all current position holdings.
        
        Returns:
            Sequence of Position entities representing current holdings
            
        Raises:
            DataAccessError: Storage system failure

        """
        ...
    
    def save_positions(self, positions: Sequence[Position]) -> None:
        """Atomically persist position updates.
        
        Args:
            positions: Complete set of positions to persist
            
        Raises:
            DataAccessError: Storage system failure
            ConcurrencyError: Optimistic lock violation

        """
        ...
    
    def get_position(self, symbol: Symbol) -> Position | None:
        """Get specific position by symbol.
        
        Args:
            symbol: Symbol to lookup
            
        Returns:
            Position if held, None if no position
            
        Raises:
            DataAccessError: Storage system failure

        """
        ...


class PlanPublisherPort(Protocol):
    """Port for publishing rebalance plans to Execution context.
    
    Responsibilities:
    - Deliver RebalancePlanContractV1 to Execution
    - Preserve correlation/causation chain
    - Handle delivery confirmations
    
    NOT responsible for:
    - Plan generation (belongs in application)
    - Order validation (Execution responsibility)
    - Risk checks (belongs in domain)
    
    Error expectations:
    - Raises PublishError for delivery failures
    
    Idempotency: Publishing same message_id twice has no additional effect
    """
    
    def publish(self, plan: RebalancePlanContractV1) -> None:
        """Publish rebalance plan for Execution.
        
        Args:
            plan: Complete plan contract with planned orders
            
        Raises:
            PublishError: Message delivery failure
            ValidationError: Invalid plan contract

        """
        ...


class ExecutionReportHandlerPort(Protocol):
    """Port for processing execution reports from Execution context.
    
    Responsibilities:
    - Receive ExecutionReportContractV1 from Execution
    - Trigger portfolio state updates
    - Handle idempotency checks
    
    NOT responsible for:
    - Fill validation (Execution responsibility)
    - Position calculations (belongs in domain)
    - Risk assessment (belongs in domain)
    
    Error expectations:
    - Raises ProcessingError for handler failures
    
    Idempotency: Processing same message_id twice has no additional effect
    """
    
    def handle_execution_report(self, report: ExecutionReportContractV1) -> None:
        """Process execution report and update portfolio state.
        
        Args:
            report: Complete execution report with fills
            
        Raises:
            ProcessingError: Report processing failure
            ValidationError: Invalid report contract

        """
        ...


class PortfolioStateRepositoryPort(Protocol):
    """Port for persisting aggregate portfolio state and metrics.
    
    Responsibilities:
    - Store portfolio valuation snapshots
    - Persist risk metrics and allocations
    - Provide historical portfolio performance
    
    NOT responsible for:
    - Metric calculations (belongs in domain)
    - Real-time valuation (computed on demand)
    - Position tracking (separate PositionRepository)
    
    Error expectations:
    - Raises DataAccessError for storage failures
    
    Idempotency: save_* methods with same data have no additional effect
    """
    
    def save_portfolio_snapshot(  # noqa: ARG002
        self, 
        portfolio_id: UUID,
        snapshot: PortfolioSnapshotVO,
        timestamp: datetime
    ) -> None:
        """Persist portfolio valuation snapshot.
        
        Args:
            portfolio_id: Portfolio identifier
            snapshot: Immutable snapshot with metrics
            timestamp: Snapshot timestamp
            
        Raises:
            DataAccessError: Storage system failure

        """
        ...
    
    def get_latest_snapshot(self, portfolio_id: UUID) -> PortfolioSnapshotVO | None:  # noqa: ARG002
        """Get most recent portfolio snapshot.
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Latest snapshot if exists, None otherwise
            
        Raises:
            DataAccessError: Storage system failure

        """
        ...


# Export list for explicit re-exports
__all__ = [
    "ExecutionReportHandlerPort",
    "PlanPublisherPort",
    "PortfolioStateRepositoryPort",
    "PositionRepositoryPort",
]