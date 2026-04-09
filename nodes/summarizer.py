"""Compatibility wrapper for summarization nodes.

This keeps existing imports working while implementation lives in services.summarization.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python nodes/summarizer.py` to resolve top-level packages.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.summarization.cli import main
from services.summarization.node import (
    summarize_brief,
    summarize_detailed,
)

__all__ = [
    "summarize_brief",
    "summarize_detailed",
]


if __name__ == "__main__":
    main()
