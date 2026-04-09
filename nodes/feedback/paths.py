"""
Đường dẫn & file lock cho việc ghi learning signals (JSONL).
"""

from __future__ import annotations

from pathlib import Path


def _project_root() -> Path:
    # nodes/feedback/ -> project root
    return Path(__file__).resolve().parents[2]


def default_learning_log_path() -> Path:
    """Đường dẫn file JSONL ghi learning signal (một dòng = một sự kiện)."""
    d = _project_root() / "api" / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "learning_signals.jsonl"


def lock_file_for(log_path: Path) -> Path:
    """File khóa đi kèm JSONL (filelock sẽ tạo / giữ lock an toàn trên Windows & Unix)."""
    return log_path.with_name(log_path.name + ".lock")


__all__ = ["default_learning_log_path", "lock_file_for"]

