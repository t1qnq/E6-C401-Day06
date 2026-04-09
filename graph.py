"""
Muc dich file: Dinh nghia LangGraph 2 Giai doan (Push Model: Teacher -> Bot -> Parent).
"""

# Load bien moi truong (.env) TRUOC KHI import langgraph
# de LangSmith tu dong nhan duoc LANGCHAIN_API_KEY
import os
from dotenv import load_dotenv
load_dotenv()  # Doc file .env tai thu muc hien tai

from typing import Annotated, TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import json

# Import các node (hiện tại đang là mock function)
from nodes.prioritizer import prioritize_notification
from nodes.summarizer import summarize_brief, summarize_detailed
from nodes.file_parser import parse_attachment_node
from nodes.feedback import handle_feedback

# ==========================================
# 1. Định Nghĩa AgentState
# ==========================================
class AgentState(TypedDict):
    # --- Input Data ---
    teacher_note: str           # Mô tả ngắn của giáo viên
    attachments: List[str]      # Danh sách file đính kèm
    notification: Optional[dict] # Object Notification Payload đầy đủ từ API
    student_profile: Optional[dict] # Object Student Profile từ API
    
    # --- AI Processing (Prioritization) ---
    extracted_text: str         
    priority_level: str         # High/Medium/Low
    priority_confidence: float  
    priority_reason: Optional[str]
    priority_source: Optional[str]
    priority_explainability: Optional[dict]
    
    # --- AI Processing (Summarization) ---
    summary: Optional[str]       # Nội dung tóm tắt (Text)
    summary_bullets: List[str]   # Các điểm chính (Bullet points)
    summary_json: Optional[dict] # Toàn bộ kết quả tóm tắt dạng JSON
    summary_tone: Optional[str]
    entities: Dict[str, Any]      # Thời gian, địa điểm trích xuất được
    
    # --- Lifecycle & Metadata ---
    summarize_status: Optional[str]
    notification_type: Optional[str]
    user_request_detail: bool    # Phụ huynh có bấm "Xem chi tiết" không?
    is_notified: bool            # Đã gửi thông báo chưa?
    messages: Annotated[list, add_messages]

# ==========================================
# 2. Logic Điều Hướng & Helper Nodes
# ==========================================
def router_start(state: AgentState) -> str:
    """Kiem tra xem co file de OCR khong"""
    if state.get("attachments") and len(state["attachments"]) > 0:
        return "parse_attachment"
    return "prioritize_notification"

def router_after_prioritize(state: AgentState) -> str:
    """Kiem tra thieu tu tin can giao vien can thiep"""
    if state.get("priority_level") == "Manual Required":
        return "teacher_intervention"
    return "scheduler"

def router_after_brief(state: AgentState) -> str:
    """Kiem tra xem phu huynh co yeu cau chi tiet khong"""
    if state.get("user_request_detail"):
        return "summarize_detailed"
    return END

def teacher_intervention(state: AgentState) -> dict:
    """Mock node mo phong giao vien xac dinh muc do uu tien (Human-in-the-loop)"""
    print("--- [Node] Teacher Intervention: Manual Priority Required ---")
    # Trong thuc te, day co the la interrupt (langgraph) hoac UI callback.
    # O day gia lap giao vien chon muc do "High"
    return {
        "priority_level": "High",
        "priority_source": "human_teacher",
        "priority_reason": "Giáo viên xác nhận thủ công do hệ thống không chắc chắn",
    }

def scheduler_node(state: AgentState) -> dict:
    """Mock node trich xuat lich hen"""
    print("--- [Node] Scheduler Running: Extracting dates/events ---")
    return {"schedule_events": [{"event": "Hop Phu Huynh", "date": "2024-05-20"}]}

# ==========================================
# 3. Khởi tạo và Nối Graph
# ==========================================
workflow = StateGraph(AgentState)

# Them cac Node
workflow.add_node("parse_attachment", parse_attachment_node)
workflow.add_node("prioritize_notification", prioritize_notification)
workflow.add_node("teacher_intervention", teacher_intervention)
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("summarize_brief", summarize_brief)
workflow.add_node("summarize_detailed", summarize_detailed)
workflow.add_node("handle_feedback", handle_feedback)

# Luong Giai doan 1: Auto-process (Teacher Push)
workflow.add_conditional_edges(START, router_start)
workflow.add_edge("parse_attachment", "prioritize_notification")

# Rẽ nhánh sau khi ưu tiên: AI tự tin -> Schedule | Không tự tin -> Đợi Giáo viên
workflow.add_conditional_edges(
    "prioritize_notification",
    router_after_prioritize,
    {
        "teacher_intervention": "teacher_intervention",
        "scheduler": "scheduler"
    }
)
workflow.add_edge("teacher_intervention", "scheduler")
workflow.add_edge("scheduler", "summarize_brief")

# Luong Giai doan 2: On-demand (Parent Click)
workflow.add_conditional_edges(
    "summarize_brief", 
    router_after_brief,
    {
        "summarize_detailed": "summarize_detailed",
        END: END
    }
)

workflow.add_edge("summarize_detailed", "handle_feedback")
workflow.add_edge("handle_feedback", END)

# ==========================================
# 4. Biên dịch Graph (Compile)
# ==========================================
app = workflow.compile()

# ==========================================
# 5. Hàm Test Local
# ==========================================
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
