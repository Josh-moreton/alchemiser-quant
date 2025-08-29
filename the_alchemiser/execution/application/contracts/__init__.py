"""Business Unit: order execution/placement; Status: current.

Execution application contracts for cross-context communication.

This package provides versioned application-layer contracts that enable
clean communication from Execution context to other bounded contexts without
exposing internal domain objects.
"""

from __future__ import annotations

from .execution_report_contract_v1 import (
    ExecutionReportContractV1,
    FillV1,
    execution_report_from_domain,
)

__all__ = [
    "ExecutionReportContractV1",
    "FillV1",
    "execution_report_from_domain",
]