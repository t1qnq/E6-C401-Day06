"""CLI helper for manual summarizer testing."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from services.summarization.io_utils import load_notification_from_json
from services.summarization.node import summarize_brief, summarize_detailed


def main() -> None:
    parser = argparse.ArgumentParser(description="Test 2 summarizer node (brief/detailed) with JSON notifications input.")
    default_json = Path(__file__).resolve().parents[2] / "api" / "mock_data" / "mock_data.json"
    parser.add_argument("--json", type=str, default=str(default_json), help="Path to notifications JSON")
    parser.add_argument("--notification-id", type=str, default="", help="Select notification by id")
    parser.add_argument("--index", type=int, default=0, help="Select notification by index")
    parser.add_argument("--mode", choices=["brief", "detailed", "both"], default="both", help="Summary mode")
    parser.add_argument("--model", type=str, default=os.getenv("OPENROUTER_MODEL", "minimax/minimax-m2.5:free"), help="OpenRouter model")
    parser.add_argument("--local-only", action="store_true", help="Disable LLM and force fallback")
    args = parser.parse_args()

    if not os.path.exists(args.json):
        print(f"Khong tim thay file JSON: {args.json}")
        return

    try:
        notif = load_notification_from_json(args.json, args.notification_id or None, args.index)
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
        out = summarize_brief(base_state)
        print("=== BRIEF SUMMARY ===")
        print(out.get("summary", ""))
        print("\n=== BRIEF JSON ===")
        print(json.dumps(out.get("summary_json", {}), ensure_ascii=False, indent=2))
        print()

    if args.mode in ["detailed", "both"]:
        out = summarize_detailed(base_state)
        print("=== DETAILED SUMMARY ===")
        print(out.get("summary", ""))
        print("\n=== DETAILED JSON ===")
        print(json.dumps(out.get("summary_json", {}), ensure_ascii=False, indent=2))
        print()
