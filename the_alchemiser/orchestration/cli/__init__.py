"""Business Unit: orchestration | Status: current.

Command-Line Interface orchestration components.

This module contains CLI components that orchestrate user interactions and coordinate
cross-module workflows through command-line interfaces. These components belong in
orchestration as they coordinate between business units rather than being shared utilities.

Exports:
    - app: Main CLI application (Typer app)
"""

# Lazy imports to avoid missing dependencies during import
__all__ = [
    "app",
]


def __getattr__(name: str):
    """Lazy import for CLI components."""
    if name == "app":
        from .cli import app
        return app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
