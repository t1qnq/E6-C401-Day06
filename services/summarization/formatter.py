"""Normalization and fallback formatting for summarization output."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from core.constants.summarization import BRIEF_MAX_POINTS
from services.summarization.io_utils import extract_pdf_link


def normalize_summary_json(
    raw: Dict[str, Any],
    notification: Dict[str, Any],
    source_text: str,
    mode: str,
) -> Dict[str, Any]:
    result = dict(raw or {})
    raw_result = result.get("result")

    if mode == "brief":
        points = raw_result if isinstance(raw_result, list) else []
        clean_points: List[str] = []
        seen = set()
        for p in points:
            item = re.sub(r"\s+", " ", str(p)).strip(" -\t")
            if not item:
                continue
            marker = item.lower()
            if marker in seen:
                continue
            seen.add(marker)
            clean_points.append(item)
            if len(clean_points) >= BRIEF_MAX_POINTS:
                break
        if not clean_points:
            clean_points = ["Thong bao can duoc xem chi tiet trong noi dung goc."]
        summary_value: Any = clean_points
    else:
        paragraph = str(raw_result if isinstance(raw_result, str) else "").strip()
        paragraph = re.sub(r"\s+", " ", paragraph)
        if not paragraph:
            paragraph = "Thong bao da duoc tiep nhan, vui long xem chi tiet noi dung goc de thuc hien dung yeu cau."
        summary_value = paragraph

    return {
        "sender": str(notification.get("sender") or ""),
        "noti_id": str(notification.get("id") or ""),
        "content": str(notification.get("content") or source_text or ""),
        "summarization": {
            "mode": mode,
            "result": summary_value,
            "pdf_link": extract_pdf_link(notification),
        },
    }


def fallback_summary_json(
    notification: Dict[str, Any],
    text: str,
    mode: str,
) -> Dict[str, Any]:
    content = re.sub(r"\s+", " ", str(notification.get("content") or text or "")).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
    if not sentences and content:
        sentences = [content]

    points: List[str] = []
    for sentence in sentences:
        clean = re.sub(r"\s+", " ", sentence).strip()
        if not clean:
            continue
        if any(clean.lower() == old.lower() for old in points):
            continue
        points.append(clean)
        if len(points) >= BRIEF_MAX_POINTS:
            break

    if not points:
        points = ["Vui long xem noi dung thong bao de biet chi tiet."]

    paragraph = " ".join(sentences[:3]).strip()
    if not paragraph:
        paragraph = "Vui long xem noi dung thong bao de biet chi tiet."

    summary_value: Any = points if mode == "brief" else paragraph
    return {
        "sender": str(notification.get("sender") or ""),
        "noti_id": str(notification.get("id") or ""),
        "content": str(notification.get("content") or text or ""),
        "summarization": {
            "mode": mode,
            "result": summary_value,
            "pdf_link": extract_pdf_link(notification),
        },
    }


def apply_result(
    state: Dict[str, Any],
    summary_json: Dict[str, Any],
    status: str,
    warnings: List[str],
    tone_profile: Dict[str, Any],
    notif_type: str,
) -> Dict[str, Any]:
    summarization = summary_json.get("summarization") if isinstance(summary_json.get("summarization"), dict) else {}
    mode = str(summarization.get("mode") or "brief")
    result_value = summarization.get("result")

    points = result_value if isinstance(result_value, list) else []
    paragraph = str(result_value if isinstance(result_value, str) else "").strip()

    if mode == "brief":
        summary_text = "\n".join(
            f"- {re.sub(r'\\s+', ' ', str(p)).strip()}"
            for p in points[:BRIEF_MAX_POINTS]
            if str(p).strip()
        )
    else:
        summary_text = paragraph

    entities = {"thoi_gian": None, "dia_diem": None, "so_tien": None, "han_chot": None, "hanh_dong": []}

    state.update(
        {
            "summary": summary_text,
            "summary_json": summary_json,
            "summary_bullets": points[:BRIEF_MAX_POINTS],
            "entities": entities,
            "notification_type": notif_type,
            "summary_tone": tone_profile.get("tone", "trung_tinh"),
            "receiver_scope": tone_profile.get("scope", "unknown"),
            "receiver_ids": tone_profile.get("receiver_ids", []),
            "summary_mode": mode,
            "summarize_status": status,
            "summarize_warnings": warnings,
        }
    )
    return state
