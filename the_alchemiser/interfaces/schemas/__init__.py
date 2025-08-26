"""Schemas package for DTOs used at system boundaries.

This package contains Pydantic models for data transfer objects (DTOs) used by
the application layer and interfaces. These DTOs provide type safety and validation
for data exchanged at system boundaries while keeping the domain layer framework-free.

Modules:
- orders: Order validation and processing DTOs
- tracking: Strategy tracking and P&L DTOs
- cli: Command-line interface DTOs
- errors: Error reporting and notification DTOs
- reporting: Dashboard, metrics, and email DTOs
- execution: Trading execution and integration DTOs
"""
