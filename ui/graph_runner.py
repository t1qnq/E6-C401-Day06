import os
import time
from typing import Any, Dict, Generator

# Import the main graph, or catch import errors to fallback
try:
    from graph import app as langgraph_app
    HAS_GRAPH = True
except ImportError:
    HAS_GRAPH = False


def check_api_keys() -> bool:
    """Check if necessary API keys are present."""
    if os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"):
        return True
    return False

def mock_prioritize(text: str) -> Dict[str, Any]:
    """Fallback mock for prioritize_notification when no API keys are present."""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ["khẩn", "gấp", "emergency", "nghỉ học", "đánh nhau", "sốt"]):
        level = "High"
        confidence = 0.95
        reason = "Matched mock high priority keywords."
    elif any(k in text_lower for k in ["họp phụ huynh", "kiểm tra", "kết quả", "học phí"]):
        level = "Medium"
        confidence = 0.8
        reason = "Matched mock medium priority keywords."
    else:
        level = "Low"
        confidence = 0.7
        reason = "No specific rules matched (mock default)."

    return {
        "priority_level": level,
        "priority_confidence": confidence,
        "priority_reason": reason,
        "priority_explainability": {
            "summary": reason,
            "source": "mock_rule",
            "evidence": ["fallback_mock_used"]
        }
    }

def mock_summarize(text: str, mode: str) -> Dict[str, Any]:
    """Fallback mock for summarize nodes."""
    from services.summarization.formatter import fallback_summary_json
    from services.summarization.io_utils import notification_type, tone_profile
    
    # Just creating a dummy notification structure
    notif = {"title": "Trích xuất", "content": text, "category": "general", "receiver_scope": "all"}
    
    summary_json = fallback_summary_json(notification=notif, text=text, mode=mode)
    
    points = summary_json.get("summarization", {}).get("result", [])
    if isinstance(points, list):
        summary_text = "\\n".join(f"- {p}" for p in points)
        summary_bullets = points
    else:
        summary_text = str(points)
        summary_bullets = []
        
    return {
        "summary": summary_text,
        "summary_bullets": summary_bullets,
        "summary_mode": mode
    }


def run_phase1_generator(state: dict) -> Generator[Dict[str, Any], None, None]:
    """Runs phase 1 (Auto Push) and yields node execution states."""
    
    start_time = time.time()
    
    if HAS_GRAPH and check_api_keys():
        # Real graph execution
        # Yield each event step for streaming
        for event in langgraph_app.stream(state):
            yield {"type": "real_step", "event": event}
            # Need to capture final state deeply if needed, but standard langgraph yields nodes
        
        # Approximate metrics for real graph
        metrics = state.get("_performance_metrics", {})
        metrics["phase1_latency"] = time.time() - start_time
        metrics["fallback_used"] = False
        state["_performance_metrics"] = metrics
        
    else:
        # Mock execution timeline (no API key → dùng mock prioritize/summarize,
        # nhưng vẫn parse file thật nếu có attachment)
        time.sleep(0.5)

        has_attachment = bool(state.get("attachment"))
        text = state.get("teacher_note", "") or ""

        if has_attachment:
            att = state["attachment"]
            fname = att.get("file_name", "file")

            # Gọi parse_attachment thật để extract text từ bytes thực
            try:
                from nodes.file_parser import parse_attachment
                parse_result = parse_attachment(
                    file=att.get("file", b""),
                    mime_type=att.get("mime_type", "application/octet-stream"),
                    file_name=fname,
                )
                extracted = parse_result.get("content", "")
                if extracted:
                    text = (text + "\n" + extracted).strip() if text else extracted
                    state["extracted_text"] = extracted
                    yield {"type": "mock_step", "node": "parse_attachment", "status": "success",
                           "desc": f"✅ Trích xuất thành công: {fname} ({len(extracted)} ký tự)"}
                else:
                    err = parse_result.get("error") or {}
                    yield {"type": "mock_step", "node": "parse_attachment", "status": "warning",
                           "desc": f"⚠️ Không đọc được nội dung từ {fname}: {err.get('message', 'unknown')}"}
            except Exception as exc:
                yield {"type": "mock_step", "node": "parse_attachment", "status": "error",
                       "desc": f"❌ Lỗi khi parse {fname}: {exc}"}


        time.sleep(1)
        # Mock prioritize
        p_res = mock_prioritize(text)
        state.update(p_res)
        yield {"type": "mock_step", "node": "prioritize_notification", "status": "success", "desc": f"Phân loại ưu tiên: {p_res['priority_level']}", "data": p_res}
        
        time.sleep(1)
        # Mock summarize (Brief)
        s_res = mock_summarize(text, mode="brief")
        state.update(s_res)
        yield {"type": "mock_step", "node": "summarize_brief", "status": "success", "desc": "Đã tạo tóm tắt ngắn."}
        
        state["extracted_text"] = text
        
        metrics = state.get("_performance_metrics", {})
        metrics["phase1_latency"] = time.time() - start_time
        metrics["fallback_used"] = True
        state["_performance_metrics"] = metrics
        
        yield {"type": "final_state", "state": state}

def run_phase2_generator(state: dict) -> Generator[Dict[str, Any], None, None]:
    """Runs phase 2 (On-demand) and yields node execution states."""
    
    start_time = time.time()
    
    if HAS_GRAPH and check_api_keys():
        for event in langgraph_app.stream(state):
            yield {"type": "real_step", "event": event}
        
        metrics = state.get("_performance_metrics", {})
        metrics["phase2_latency"] = time.time() - start_time
        state["_performance_metrics"] = metrics
    else:
        time.sleep(1)
        # Mock summarize detailed
        text = state.get("extracted_text", "")
        s_res = mock_summarize(text, mode="detailed")
        state.update(s_res)
        yield {"type": "mock_step", "node": "summarize_detailed", "status": "success", "desc": "Tạo tóm tắt chi tiết 1 đoạn văn."}
        
        time.sleep(0.5)
        # Mock scheduler
        events = [{"event": "Họp phụ huynh", "date": "2024-05-20"}]
        state["schedule_events"] = events
        yield {"type": "mock_step", "node": "scheduler", "status": "success", "desc": "Trích xuất lịch kiện.", "data": {"events": events}}
        
        metrics = state.get("_performance_metrics", {})
        metrics["phase2_latency"] = time.time() - start_time
        state["_performance_metrics"] = metrics
        
        yield {"type": "final_state", "state": state}
