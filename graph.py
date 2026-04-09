from typing import Annotated, TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import json
from nodes.prioritizer import prioritize_notification
from nodes.summarizer import summarize_brief, summarize_detailed
from nodes.file_parser import parse_attachment
from nodes.feedback import handle_feedback

class AgentState(TypedDict):
    teacher_note: str           
    attachments: List[str]     
    
    extracted_text: str         
    priority_level: str        
    priority_confidence: float  
    
    brief_summary: str           # Tom tat 1 dong (Auto)
    detailed_summary: List[str]  # Tom tat chi tiet (On-demand)
    schedule_events: List[dict]  # Lich hen trich xuat (On-demand)

    user_request_detail: bool    # Phu huynh co bam "Xem chi tiet" khong?
    is_notified: bool            # Da gui thong bao cho phu huynh chua?
    messages: Annotated[list, add_messages]

def router_start(state: AgentState) -> str:
    """Kiem tra xem co file de OCR khong"""
    if state.get("attachments") and len(state["attachments"]) > 0:
        return "parse_attachment"
    return "prioritize_notification"

def router_after_brief(state: AgentState) -> str:
    """Kiem tra xem phu huynh co yeu cau chi tiet khong"""
    if state.get("user_request_detail"):
        return "summarize_detailed"
    return END

def scheduler_node(state: AgentState) -> dict:
    """Mock node trich xuat lich hen"""
    print("--- [Node] Scheduler Running: Extracting dates/events ---")
    return {"schedule_events": [{"event": "Hop Phu Huynh", "date": "2024-05-20"}]}

workflow = StateGraph(AgentState)

workflow.add_node("parse_attachment", parse_attachment)
workflow.add_node("prioritize_notification", prioritize_notification)
workflow.add_node("summarize_brief", summarize_brief)
workflow.add_node("summarize_detailed", summarize_detailed)
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("handle_feedback", handle_feedback)

workflow.add_conditional_edges(START, router_start)
workflow.add_edge("parse_attachment", "prioritize_notification")
workflow.add_edge("prioritize_notification", "summarize_brief")

workflow.add_conditional_edges(
    "summarize_brief", 
    router_after_brief,
    {
        "summarize_detailed": "summarize_detailed",
        END: END
    }
)

workflow.add_edge("summarize_detailed", "scheduler")
workflow.add_edge("scheduler", "handle_feedback")
workflow.add_edge("handle_feedback", END)

app = workflow.compile()

def test_push_model():
    """Gia lap: Giao vien day tin -> He thong tu dong tao Brief Summary"""
    print("\n[PHASE 1: Teacher Push - Auto Processing]")
    initial_state = {
        "teacher_note": "Thong bao hop phu huynh cuoi ky",
        "attachments": ["notif_pdf.pdf"],
        "user_request_detail": False, # Ban dau chua bam xem chi tiet
    }
    for event in app.stream(initial_state):
        for k, v in event.items():
            print(f"Node completed: {k}")

def test_parent_click():
    """Gia lap: Phu huynh bam nut 'Xem chi tiet'"""
    print("\n[PHASE 2: Parent Interactive - Deep Dive]")
    # Gia su state cu da co brief summary
    state_with_request = {
        "teacher_note": "Thong bao hop phu huynh cuoi ky",
        "attachments": ["notif_pdf.pdf"],
        "user_request_detail": True, # Phu huynh bam nut
    }
    for event in app.stream(state_with_request):
        for k, v in event.items():
            print(f"Node completed: {k}")

if __name__ == "__main__":
    test_push_model()
    test_parent_click()
