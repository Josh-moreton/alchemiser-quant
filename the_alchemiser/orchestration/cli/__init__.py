"""Business Unit: orchestration | Status: current.

Command-Line Interface orchestration components.

This module contains CLI components that orchestrate user interactions and coordinate
cross-module workflows through command-line interfaces. These components belong in
orchestration as they coordinate between business units rather than being shared utilities.

Exports:
    - app: Main CLI application (Typer app)
"""

from .cli import app

__all__ = [
    "app",
]
