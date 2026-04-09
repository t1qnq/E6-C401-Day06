import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

from config.prioritization_runtime import load_runtime_config

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]{2,}")
LEVELS = ("HIGH", "MEDIUM", "LOW")


class FeedbackLearner:
    """Persist feedback signals and periodically rebuild learned keyword dictionary."""

    def __init__(self) -> None:
        self._last_rebuild_ts = 0.0

    def _cfg(self) -> Dict[str, Any]:
        return load_runtime_config().get("feedback_learning", {})

    def _feedback_log_path(self) -> Path:
        return Path(str(self._cfg().get("feedback_log_path", "data/feedback/priority_feedback.jsonl")))

    def _learned_keywords_path(self) -> Path:
        return Path(str(self._cfg().get("learned_keywords_path", "data/feedback/learned_keywords.json")))

    def _ensure_parent(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def append_feedback_signal(self, signal: Dict[str, Any]) -> None:
        if not self._cfg().get("enabled", True):
            return

        path = self._feedback_log_path()
        self._ensure_parent(path)

        safe_signal = dict(signal)
        safe_signal["created_at"] = int(time.time())
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe_signal, ensure_ascii=True) + "\n")

    def _tokenize(self, text: str, ignored: Iterable[str], min_len: int) -> list[str]:
        lowered = text.lower()
        ignored_set = set(ignored)
        tokens = [tok for tok in TOKEN_PATTERN.findall(lowered) if len(tok) >= min_len]
        return [tok for tok in tokens if tok not in ignored_set]

    def _read_feedback_lines(self) -> list[Dict[str, Any]]:
        path = self._feedback_log_path()
        if not path.exists():
            return []

        rows: list[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        return rows

    def rebuild_learned_keywords(self) -> Dict[str, list[str]]:
        cfg = self._cfg()
        ignored_tokens = cfg.get("ignored_tokens", [])
        min_token_length = int(cfg.get("min_token_length", 4))
        min_freq = int(cfg.get("min_keyword_frequency", 2))
        max_per_level = int(cfg.get("max_keywords_per_level", 60))

        counters = {level: Counter() for level in LEVELS}
        for row in self._read_feedback_lines():
            corrected = str(row.get("corrected_priority", "")).upper()
            text = str(row.get("text", ""))
            if corrected not in LEVELS or not text.strip():
                continue

            for token in self._tokenize(text, ignored=ignored_tokens, min_len=min_token_length):
                counters[corrected][token] += 1

        learned = {}
        for level in LEVELS:
            sorted_tokens = [
                token for token, freq in counters[level].most_common() if freq >= min_freq
            ]
            learned[level] = sorted_tokens[:max_per_level]

        out_path = self._learned_keywords_path()
        self._ensure_parent(out_path)
        out_path.write_text(json.dumps(learned, ensure_ascii=True, indent=2), encoding="utf-8")
        self._last_rebuild_ts = time.time()
        return learned

    def maybe_rebuild(self) -> None:
        if not self._cfg().get("enabled", True):
            return

        interval = int(self._cfg().get("rebuild_interval_seconds", 1800))
        now = time.time()
        if now - self._last_rebuild_ts < interval:
            return
        self.rebuild_learned_keywords()

    def load_learned_keywords(self) -> Dict[str, set[str]]:
        path = self._learned_keywords_path()
        if not path.exists():
            return {"HIGH": set(), "MEDIUM": set(), "LOW": set()}

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {"HIGH": set(), "MEDIUM": set(), "LOW": set()}

        return {
            "HIGH": set(payload.get("HIGH", [])),
            "MEDIUM": set(payload.get("MEDIUM", [])),
            "LOW": set(payload.get("LOW", [])),
        }


feedback_learner = FeedbackLearner()
