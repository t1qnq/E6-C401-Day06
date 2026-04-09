"""
Lưu trữ learning signals (JSONL append + filelock).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filelock import FileLock

from .paths import lock_file_for


def append_jsonl(record: dict[str, Any], path: Path) -> None:
    """
    Ghi một dòng JSON vào file JSONL.

    Dùng **FileLock** quanh toàn bộ mở-append để tránh interleaving / mất dòng khi
    nhiều tiến trình / thread ghi cùng lúc (Streamlit + API).
    """
    line = json.dumps(record, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = lock_file_for(path)
    with FileLock(lock_path, timeout=60):
        with path.open("a", encoding="utf-8") as f:
            f.write(line)


__all__ = ["append_jsonl"]

