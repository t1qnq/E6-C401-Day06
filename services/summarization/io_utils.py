"""I/O and metadata helpers for summarization."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from core.constants.summarization import CATEGORY_TO_TYPE, TONE_BY_SCOPE


def resolve_notification(state: Dict[str, Any]) -> Dict[str, Any]:
    notif = state.get("notification")
    if isinstance(notif, dict):
        return notif

    fields = [
        "id",
        "sender",
        "timestamp",
        "title",
        "content",
        "category",
        "receiver_scope",
        "receiver_ids",
        "attachments",
    ]
    out: Dict[str, Any] = {}
    for key in fields:
        if key in state:
            out[key] = state.get(key)

    if isinstance(out.get("receiver_ids"), list):
        out["receiver_ids"] = [str(x) for x in out["receiver_ids"]]
    else:
        out["receiver_ids"] = []
    return out


def notification_text(notification: Dict[str, Any], state: Dict[str, Any]) -> str:
    chunks: List[str] = []

    for key in ("title", "content", "text", "body", "message", "markdown"):
        value = notification.get(key)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    for key in ("notification_text", "content", "text", "notification_markdown", "markdown_text"):
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    seen = set()
    deduped = []
    for item in chunks:
        marker = re.sub(r"\s+", " ", item.strip().lower())
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)

    return "\n".join(deduped).strip()


def tone_profile(notification: Dict[str, Any]) -> Dict[str, Any]:
    scope = str(notification.get("receiver_scope") or "").strip().lower()
    receiver_ids = notification.get("receiver_ids")
    if not isinstance(receiver_ids, list):
        receiver_ids = []
    receiver_ids = [str(x) for x in receiver_ids]

    base = TONE_BY_SCOPE.get(scope, {"tone": "trung_tinh", "audience": "gui den nhom nguoi nhan"})
    return {
        "scope": scope or "unknown",
        "receiver_ids": receiver_ids,
        "tone": base["tone"],
        "audience": base["audience"],
    }


def notification_type(notification: Dict[str, Any], text: str) -> str:
    category = str(notification.get("category") or "").strip().lower()
    if category in CATEGORY_TO_TYPE:
        return CATEGORY_TO_TYPE[category]

    normalized = text.lower()
    if any(k in normalized for k in ("hoc phi", "phi", "thanh toan", "chuyen khoan")):
        return "hoc_phi"
    if any(k in normalized for k in ("tham quan", "da ngoai", "ngoai khoa")):
        return "da_ngoai"
    if any(k in normalized for k in ("lich", "kiem tra", "thi", "hop phu huynh")):
        return "lich_hoc"
    return "unknown"


def extract_pdf_link(notification: Dict[str, Any]) -> str:
    attachments = notification.get("attachments")
    if not isinstance(attachments, list):
        return ""

    for item in attachments:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        item_type = str(item.get("type") or "").strip().lower()
        if item_type == "pdf" or url.lower().endswith(".pdf"):
            return url

    for item in attachments:
        if isinstance(item, dict) and str(item.get("url") or "").strip():
            return str(item.get("url") or "").strip()
    return ""


def load_notification_from_json(json_path: str, notif_id: str | None, index: int) -> Dict[str, Any]:
    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    items = payload.get("notifications", []) if isinstance(payload, dict) else []
    if not isinstance(items, list) or not items:
        raise ValueError("Khong tim thay danh sach notifications trong file JSON.")

    if notif_id:
        for item in items:
            if isinstance(item, dict) and str(item.get("id")) == notif_id:
                return item
        raise ValueError(f"Khong tim thay notification id={notif_id}.")

    if index < 0 or index >= len(items):
        raise ValueError(f"Index notification khong hop le: {index}.")
    if not isinstance(items[index], dict):
        raise ValueError("Notification tai index da cho khong phai object.")
    return items[index]
