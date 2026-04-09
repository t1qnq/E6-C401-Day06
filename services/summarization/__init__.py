"""Summarization service package."""

from services.summarization.node import (
    summarize_brief,
    summarize_detailed,
)

__all__ = [
    "summarize_brief",
    "summarize_detailed",
]
