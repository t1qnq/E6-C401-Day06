"""Prompt-first summarizer node for school notifications (JSON input/output)."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv


load_dotenv()

State = Dict[str, Any]

BRIEF_MAX_POINTS = 3

TONE_BY_SCOPE = {
    "student": {"tone": "ca_nhan", "audience": "gui den mot phu huynh"},
    "class": {"tone": "tap_the_lop", "audience": "gui den mot giao vien lop cu the"},
    "grade": {"tone": "tap_the_khoi", "audience": "gui den mot giao vien khoi hoc"},
    "all": {"tone": "toan_truong", "audience": "gui den toan truong"},
}

CATEGORY_TO_TYPE = {
    "finance": "hoc_phi",
    "extracurricular": "da_ngoai",
    "academic": "lich_hoc",
    "emergency": "unknown",
    "health": "unknown",
}


def summarize_notification(state: State) -> State:
    """Backward-compatible entrypoint, default to brief mode."""
    return summarize_notification_brief(state)


def summarize_notification_brief(state: State) -> State:
    """Summarize into max 3 key points (JSON output included)."""
    return _summarize_with_mode(state, mode="brief")


def summarize_notification_detailed(state: State) -> State:
    """Summarize into one paragraph (JSON output included)."""
    return _summarize_with_mode(state, mode="detailed")


def _summarize_with_mode(state: State, mode: str) -> State:
    updated = dict(state or {})
    warnings: List[str] = []

    notification = _resolve_notification(updated)
    text = _notification_text(notification, updated)
    tone_profile = _tone_profile(notification)
    notif_type = _notification_type(notification, text)

    if not text.strip():
        summary_json = _fallback_summary_json(
            notification=notification,
            text="",
            mode=mode,
            tone_profile=tone_profile,
            notif_type=notif_type,
            reason="missing_input",
        )
        return _apply_result(updated, summary_json, "fallback", ["missing_input"], tone_profile, notif_type)

    force_local = bool(updated.get("disable_llm") or updated.get("local_only"))
    model = str(updated.get("openrouter_model") or os.getenv("OPENROUTER_MODEL", "minimax2.5:free"))

    llm_status, llm_payload = _llm_summarize_json(
        notification=notification,
        text=text,
        mode=mode,
        tone_profile=tone_profile,
        notif_type=notif_type,
        model=model,
        force_local=force_local,
    )

    if llm_status == "ok":
        summary_json = _normalize_summary_json(
            raw=llm_payload,
            notification=notification,
            source_text=text,
            mode=mode,
            tone_profile=tone_profile,
            notif_type=notif_type,
        )
        warnings.append("source:llm")
        return _apply_result(updated, summary_json, "success", warnings, tone_profile, notif_type)

    warnings.append(f"llm:{llm_status}")
    summary_json = _fallback_summary_json(
        notification=notification,
        text=text,
        mode=mode,
        tone_profile=tone_profile,
        notif_type=notif_type,
        reason=llm_status,
    )
    return _apply_result(updated, summary_json, "fallback", warnings, tone_profile, notif_type)


def _resolve_notification(state: State) -> Dict[str, Any]:
    notif = state.get("notification")
    if isinstance(notif, dict):
        return notif

    fields = ["id", "sender", "timestamp", "title", "content", "category", "receiver_scope", "receiver_ids", "attachments"]
    out: Dict[str, Any] = {}
    for key in fields:
        if key in state:
            out[key] = state.get(key)

    if isinstance(out.get("receiver_ids"), list):
        out["receiver_ids"] = [str(x) for x in out["receiver_ids"]]
    else:
        out["receiver_ids"] = []

    return out


def _notification_text(notification: Dict[str, Any], state: State) -> str:
    chunks: List[str] = []

    for key in ["title", "content", "text", "body", "message", "markdown"]:
        value = notification.get(key)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    for key in ["notification_text", "content", "text", "notification_markdown", "markdown_text"]:
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


def _tone_profile(notification: Dict[str, Any]) -> Dict[str, Any]:
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


def _notification_type(notification: Dict[str, Any], text: str) -> str:
    category = str(notification.get("category") or "").strip().lower()
    if category in CATEGORY_TO_TYPE:
        return CATEGORY_TO_TYPE[category]

    normalized = text.lower()
    if any(k in normalized for k in ["hoc phi", "phi", "thanh toan", "chuyen khoan"]):
        return "hoc_phi"
    if any(k in normalized for k in ["tham quan", "da ngoai", "ngoai khoa"]):
        return "da_ngoai"
    if any(k in normalized for k in ["lich", "kiem tra", "thi", "hop phu huynh"]):
        return "lich_hoc"
    return "unknown"


def _llm_summarize_json(
    notification: Dict[str, Any],
    text: str,
    mode: str,
    tone_profile: Dict[str, Any],
    notif_type: str,
    model: str,
    force_local: bool,
) -> Tuple[str, Dict[str, Any]]:
    if force_local:
        return "disabled", {}

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return "no_api_key", {}

    try:
        module = importlib.import_module("langchain_openai")
        ChatOpenAI = getattr(module, "ChatOpenAI")
    except Exception:
        return "missing_dependency", {}

    system_prompt = (
        "You are a school-notification summarization assistant. "
        "Given a notification JSON input, return valid JSON only, with no markdown and no explanations. "
        "Important: all natural-language output content must be in Vietnamese. "
        "Mode brief: result must be a list with at most 3 concise key points, prioritizing action, deadline, and amount. "
        "Mode detailed: result must be exactly one concise paragraph of 2-4 sentences, with tone aligned to receiver_scope. "
        "Required schema:\n"
        "{\n"
        "  \"result\": [\"string\"] or \"string\" (depending on mode),\n"
        "  \"confidence\": \"high|medium|low\"\n"
        "}"
    )

    payload = {
        "mode": mode,
        "expected_notification_type": notif_type,
        "tone_profile": tone_profile,
        "notification": notification,
        "text": text,
    }

    try:
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
        )
        response = llm.invoke(
            [
                ("system", system_prompt),
                ("human", json.dumps(payload, ensure_ascii=False)),
            ]
        )
        content = response.content if hasattr(response, "content") else str(response)
        parsed = _parse_llm_json(str(content))
        if not isinstance(parsed, dict):
            return "invalid_json", {}
        return "ok", parsed
    except Exception:
        return "llm_error", {}


def _parse_llm_json(content: str) -> Dict[str, Any]:
    text = content.strip()
    if not text:
        return {}

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_summary_json(
    raw: Dict[str, Any],
    notification: Dict[str, Any],
    source_text: str,
    mode: str,
    tone_profile: Dict[str, Any],
    notif_type: str,
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
            "pdf_link": _extract_pdf_link(notification),
        },
    }


def _fallback_summary_json(
    notification: Dict[str, Any],
    text: str,
    mode: str,
    tone_profile: Dict[str, Any],
    notif_type: str,
    reason: str,
) -> Dict[str, Any]:
    _ = (tone_profile, notif_type, reason)
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
            "pdf_link": _extract_pdf_link(notification),
        },
    }


def _apply_result(
    state: State,
    summary_json: Dict[str, Any],
    status: str,
    warnings: List[str],
    tone_profile: Dict[str, Any],
    notif_type: str,
) -> State:
    summarization = summary_json.get("summarization") if isinstance(summary_json.get("summarization"), dict) else {}
    mode = str(summarization.get("mode") or "brief")
    result_value = summarization.get("result")

    points = result_value if isinstance(result_value, list) else []
    paragraph = str(result_value if isinstance(result_value, str) else "").strip()

    if mode == "brief":
        summary_text = "\n".join(f"- {re.sub(r'\\s+', ' ', str(p)).strip()}" for p in points[:BRIEF_MAX_POINTS] if str(p).strip())
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


def _extract_pdf_link(notification: Dict[str, Any]) -> str:
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


def _load_notification_from_json(json_path: str, notif_id: str | None, index: int) -> Dict[str, Any]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Test 2 summarizer node (brief/detailed) with JSON notifications input.")
    default_json = Path(__file__).resolve().parents[1] / "api" / "mock_data" / "mock_data.json"
    parser.add_argument("--json", type=str, default=str(default_json), help="Path to notifications JSON")
    parser.add_argument("--notification-id", type=str, default="", help="Select notification by id")
    parser.add_argument("--index", type=int, default=0, help="Select notification by index")
    parser.add_argument("--mode", choices=["brief", "detailed", "both"], default="both", help="Summary mode")
    parser.add_argument("--model", type=str, default=os.getenv("OPENROUTER_MODEL", "minimax2.5:free"), help="OpenRouter model")
    parser.add_argument("--local-only", action="store_true", help="Disable LLM and force fallback")
    args = parser.parse_args()

    if not os.path.exists(args.json):
        print(f"Khong tim thay file JSON: {args.json}")
        return

    try:
        notif = _load_notification_from_json(args.json, args.notification_id or None, args.index)
    except Exception as exc:  # noqa: BLE001
        print(f"Doc JSON that bai: {exc}")
        return

    print(f"=== INPUT NOTIFICATION ===\nid={notif.get('id')} | title={notif.get('title')}\n")

    base_state = {
        "notification": notif,
        "openrouter_model": args.model,
        "disable_llm": args.local_only,
    }

    if args.mode in ["brief", "both"]:
        out = summarize_notification_brief(base_state)
        print("=== BRIEF SUMMARY ===")
        print(out.get("summary", ""))
        print("\n=== BRIEF JSON ===")
        print(json.dumps(out.get("summary_json", {}), ensure_ascii=False, indent=2))
        print()

    if args.mode in ["detailed", "both"]:
        out = summarize_notification_detailed(base_state)
        print("=== DETAILED SUMMARY ===")
        print(out.get("summary", ""))
        print("\n=== DETAILED JSON ===")
        print(json.dumps(out.get("summary_json", {}), ensure_ascii=False, indent=2))
        print()


__all__ = [
    "summarize_notification",
    "summarize_notification_brief",
    "summarize_notification_detailed",
]


if __name__ == "__main__":
    main()
