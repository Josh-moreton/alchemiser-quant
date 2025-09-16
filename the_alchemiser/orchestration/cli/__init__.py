"""Business Unit: orchestration | Status: current.

Command-line interface for orchestration workflows.

This package provides the CLI layer that coordinates trading workflows across
business units. The CLI belongs in orchestration because it orchestrates
complex workflows that span multiple modules rather than belonging to any 
specific business unit.

Contains:
- CLI main interface and commands
- Trading execution workflow CLI  
- Base CLI functionality and formatting
- Strategy tracking and dashboard utilities

Moved from shared/cli to orchestration/cli for proper architectural alignment.
"""

from __future__ import annotations

__all__: list[str] = []