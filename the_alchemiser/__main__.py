#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Module entry point for The Alchemiser Trading System.

Provides `python -m the_alchemiser` access. Trading runs via Lambda functions.
"""

from __future__ import annotations

import sys

from the_alchemiser.main import main

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
