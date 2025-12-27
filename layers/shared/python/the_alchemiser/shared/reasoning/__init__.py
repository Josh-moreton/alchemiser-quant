"""Business Unit: shared | Status: current.

Natural language reasoning generation for DSL strategies.

This module provides utilities for converting technical decision paths
into human-readable narratives for trading signals.
"""

from .nl_generator import NaturalLanguageGenerator
from .templates import ReasoningTemplates

__all__ = [
    "NaturalLanguageGenerator",
    "ReasoningTemplates",
]
