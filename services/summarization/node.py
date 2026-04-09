"""Public summarization node functions used by graph and app."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from services.summarization.formatter import apply_result, fallback_summary_json, normalize_summary_json
from services.summarization.io_utils import (
    notification_text,
    notification_type,
    resolve_notification,
    tone_profile,
)
from services.summarization.llm_client import llm_summarize_json

load_dotenv()

State = Dict[str, Any]


def summarize_brief(state: State) -> State:
    """Public node 1: summarize into max 3 key points."""
    return _summarize_with_mode(state, mode="brief")


def summarize_detailed(state: State) -> State:
    """Public node 2: summarize into one paragraph."""
    return _summarize_with_mode(state, mode="detailed")


def _summarize_with_mode(state: State, mode: str) -> State:
    updated = dict(state or {})
    warnings: List[str] = []

    notification = resolve_notification(updated)
    text = notification_text(notification, updated)
    tone = tone_profile(notification)
    notif_type = notification_type(notification, text)

    if not text.strip():
        summary_json = fallback_summary_json(notification=notification, text="", mode=mode)
        return apply_result(updated, summary_json, "fallback", ["missing_input"], tone, notif_type)

    force_local = bool(updated.get("disable_llm") or updated.get("local_only"))
    model = str(updated.get("openrouter_model") or os.getenv("OPENROUTER_MODEL", "minimax/minimax-m2.5:free"))
    if model.strip() == "minimax2.5:free":
        model = "minimax/minimax-m2.5:free"

    llm_status, llm_payload = llm_summarize_json(
        notification=notification,
        text=text,
        mode=mode,
        tone_profile=tone,
        notif_type=notif_type,
        model=model,
        force_local=force_local,
    )

    if llm_status == "ok":
        summary_json = normalize_summary_json(
            raw=llm_payload,
            notification=notification,
            source_text=text,
            mode=mode,
        )
        warnings.append("source:llm")
        return apply_result(updated, summary_json, "success", warnings, tone, notif_type)

    warnings.append(f"llm:{llm_status}")
    summary_json = fallback_summary_json(notification=notification, text=text, mode=mode)
    return apply_result(updated, summary_json, "fallback", warnings, tone, notif_type)
