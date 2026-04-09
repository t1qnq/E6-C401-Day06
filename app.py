import streamlit as st
import pandas as pd
import plotly.express as px

from ui.styles import apply_custom_css
from ui.components import (
    render_notification_card,
    render_priority_badge,
    render_timeline_step,
    render_explainability_panel,
    render_feedback_buttons
)
from ui.data_service import get_notifications, get_students, get_student_for_notification, get_analytics
from ui.graph_runner import run_phase1_generator, run_phase2_generator

from PIL import Image

_favicon = Image.open("static/logo-vinuni.png")

st.set_page_config(
    page_title="Vinschool Notification AI",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()

# Cache data so we don't load repeatedly on every script run
if "notifications" not in st.session_state:
    st.session_state.notifications = get_notifications()

if "eval_logs" not in st.session_state:
    st.session_state.eval_logs = []

def record_eval_log(metrics_dict: dict, priority_level: str, confidence: float):
    st.session_state.eval_logs.append({
        "latency": metrics_dict.get("phase1_latency", 0),
        "fallback_used": metrics_dict.get("fallback_used", True),
        "priority_level": priority_level,
        "confidence": confidence,
        "timestamp": pd.Timestamp.now()
    })

def page_dashboard():
    st.title("📋 Dashboard Thông Báo")
    
    st.sidebar.header("Bộ lọc tìm kiếm")
    
    # Filters
    categories = ["All"] + list(set([n.get("category", "") for n in st.session_state.notifications if n.get("category")]))
    sel_category = st.sidebar.selectbox("Category", categories)
    
    sel_priority = st.sidebar.selectbox("Priority Level", ["All", "High", "Medium", "Low"])
    
    scopes = ["All"] + list(set([n.get("receiver_scope", "") for n in st.session_state.notifications if n.get("receiver_scope")]))
    sel_scope = st.sidebar.selectbox("Receiver Scope", scopes)
    
    search_query = st.sidebar.text_input("Tìm kiếm tiêu đề/nội dung...")
    
    # Apply Filters
    filtered_data = st.session_state.notifications
    if sel_category != "All":
        filtered_data = [n for n in filtered_data if n.get("category") == sel_category]
    if sel_priority != "All":
        filtered_data = [n for n in filtered_data if n.get("_priority", "").lower() == sel_priority.lower()]
    if sel_scope != "All":
        filtered_data = [n for n in filtered_data if n.get("receiver_scope") == sel_scope]
    if search_query:
        query = search_query.lower()
        filtered_data = [n for n in filtered_data if query in n.get("title", "").lower() or query in n.get("content", "").lower()]
    
    st.markdown(f"**Hiển thị {len(filtered_data)} thông báo**")
    
    # Pagination
    items_per_page = 20
    total_pages = max(1, len(filtered_data) // items_per_page + (1 if len(filtered_data) % items_per_page > 0 else 0))
    page = st.number_input("Trang", min_value=1, max_value=total_pages, value=1)
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # Display cards
    for notif in filtered_data[start_idx:end_idx]:
        render_notification_card(notif)


def page_ai_processing():
    st.title("🤖 AI Processing Workflow")
    st.markdown("Demo ứng dụng luồng xử lý AI (Push Model) 2 Giai đoạn trên một thông báo cụ thể.")
    
    all_notifs = st.session_state.notifications
    if not all_notifs:
        st.warning("Không có dữ liệu thông báo.")
        return
        
    # Select a notification to process
    titles = [n.get("title", f"NOTIF_{i}") for i, n in enumerate(all_notifs[:50])]
    selected_idx = st.selectbox("Chọn một thông báo (50 thông báo lỗi gần nhất)", options=range(len(titles)), format_func=lambda i: titles[i])
    
    notif = all_notifs[selected_idx]
    
    st.subheader("Thông tin giáo viên nhập")
    st.info(f"**Tiêu đề:** {notif.get('title')}\\n**Nội dung gốc:** {notif.get('content')}")
    
    if st.button("▶ Chạy AI Pipeline (Phase 1)", type="primary"):
        st.session_state.current_state = {
            "teacher_note": notif.get("title"),
            "notification": notif,
            "attachments": notif.get("attachments", []),
            "student_profile": get_student_for_notification(notif),
            "user_request_detail": False
        }
        
        st.subheader("Trạng thái xử lý")
        progress_container = st.container()
        
        with progress_container:
            generator = run_phase1_generator(st.session_state.current_state)
            
            for step in generator:
                if step["type"] == "mock_step":
                    render_timeline_step(step["node"], step["status"], step["desc"], step.get("data"))
                elif step["type"] == "final_state":
                    st.session_state.current_state = step["state"]
                    current_notif = next((n for n in st.session_state.notifications if n["id"] == notif["id"]), None)
                    if current_notif:
                        current_notif["_priority"] = step["state"].get("priority_level")
                        current_notif["_brief_summary"] = step["state"].get("summary")
        
        st.success("Phase 1 hoàn tất! Thông báo đã được cập nhật ưu tiên và tóm tắt nhanh.")
        
    if "current_state" in st.session_state and "summary" in st.session_state.current_state:
        st.divider()
        st.subheader("Kết quả cho Phụ Huynh (View 1)")
        
        state = st.session_state.current_state
        render_priority_badge(state.get("priority_level"))
        st.markdown(f"**Độ tin cậy:** `{state.get('priority_confidence', 0):.2f}`")
        if "priority_explainability" in state:
            render_explainability_panel(state["priority_explainability"])
            
        st.markdown("**Tóm tắt (Brief):**")
        st.markdown(state.get("summary"))
        
        if st.button("📖 Xem Chi Tiết (Trigger Phase 2)"):
            st.session_state.current_state["user_request_detail"] = True
            
            st.subheader("Trạng thái xử lý (Phase 2)")
            with st.container():
                generator2 = run_phase2_generator(st.session_state.current_state)
                for step in generator2:
                    if step["type"] == "mock_step":
                        render_timeline_step(step["node"], step["status"], step["desc"], step.get("data"))
                    elif step["type"] == "final_state":
                        st.session_state.current_state = step["state"]
            
            st.success("Phase 2 hoàn tất!")
            
            st.divider()
            st.subheader("Chi Tiết Bổ Sung (View 2)")
            state2 = st.session_state.current_state
            
            st.markdown("**Tóm tắt (Detailed):**")
            st.write(state2.get("summary"))
            
            events = state2.get("schedule_events", [])
            if events:
                st.markdown("**Sự Kiện Trích Xuất:**")
                for e in events:
                    st.info(f"- {e.get('event')} vào {e.get('date')}")
            
            st.markdown("**Phản hồi chất lượng**")
            action = render_feedback_buttons(notif.get("id"))
            if action:
                st.write(f"Đã ghi nhận action: {action}")


def page_teacher_portal():
    st.title("👨‍🏫 Cổng Gửi Thông Báo (Teacher Portal)")
    st.markdown("Giáo viên tạo và gửi thông báo mới cho Phụ Huynh. Hệ thống AI sẽ tự động phân tích đính kèm và nội dung.")
    
    with st.container():
        st.markdown("### 📝 Soạn Thông Báo Mới")
        
        with st.form("teacher_push_form"):
            title = st.text_input("Tiêu đề thông báo", placeholder="VD: Lịch đóng học phí tháng 5")
            uploaded_file = st.file_uploader("Đính kèm tệp tin (PDF, JPG, PNG)", type=["pdf", "jpg", "png", "jpeg"])
            content = st.text_area("Nội dung (tuỳ chọn)", placeholder="Nhập thêm ghi chú của giáo viên ở đây...")
            
            submitted = st.form_submit_button("Gửi thông báo & Phân loại AI", type="primary")
            
        if submitted and (title or content or uploaded_file):
            st.markdown("---")
            st.subheader("Trạng thái xử lý AI")
            
            # Prepare state
            new_notif_payload = {
                "id": f"NEW_{len(st.session_state.notifications)}",
                "title": title or "Không có tiêu đề",
                "content": content or "",
                "sender": "Giáo viên chủ nhiệm",
                "timestamp": str(pd.Timestamp.now()),
                "receiver_scope": "all"
            }
            
            attachment_list = []
            if uploaded_file:
                attachment_list.append({
                    "name": uploaded_file.name,
                    "type": uploaded_file.type,
                    "size": uploaded_file.size
                })
                
            teacher_state = {
                "teacher_note": title + " " + content,
                "notification": new_notif_payload,
                "attachments": attachment_list,
                "student_profile": {},
                "user_request_detail": False
            }
            
            with st.container():
                generator = run_phase1_generator(teacher_state)
                final_state = {}
                for step in generator:
                    if step["type"] == "mock_step":
                        render_timeline_step(step["node"], step["status"], step["desc"], step.get("data"))
                    elif step["type"] == "final_state":
                        final_state = step["state"]
                
                if final_state:
                    # Update new notification with AI results
                    new_notif_payload["_priority"] = final_state.get("priority_level")
                    new_notif_payload["_brief_summary"] = final_state.get("summary")
                    
                    st.session_state.notifications.insert(0, new_notif_payload)
                    
                    # Log metrics
                    metrics = final_state.get("_performance_metrics", {})
                    record_eval_log(metrics, final_state.get("priority_level", "Low"), final_state.get("priority_confidence", 0.0))
                    
                    st.success("✅ Gửi thành công! AI đã phân loại xong.")
                    
                    st.markdown("### Xem trước (Phụ huynh sẽ nhận được)")
                    render_notification_card(new_notif_payload)

def page_analytics():
    st.title("📊 Thống Kê & Phân Tích")
    
    stats = get_analytics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số thông báo", stats["total_notifications"])
    
    # Priority Distribution (Mock based on random assignment for those not yet processed)
    # Since we don't run AI on all 300 upfront, we show category distribution
    
    st.subheader("Phân bố theo Danh mục (Category)")
    df_cat = pd.DataFrame(list(stats["categories"].items()), columns=["Category", "Count"])
    fig_cat = px.bar(df_cat, x="Category", y="Count", color="Category", 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0")
    st.plotly_chart(fig_cat, use_container_width=True)
    
    st.subheader("Phân bố theo Tầm ảnh hưởng (Scope)")
    df_scope = pd.DataFrame(list(stats["scopes"].items()), columns=["Scope", "Count"])
    fig_scope = px.pie(df_scope, names="Scope", values="Count", 
                       color_discrete_sequence=px.colors.qualitative.Set3)
    fig_scope.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0")
    st.plotly_chart(fig_scope, use_container_width=True)

def page_evaluation():
    st.title("📈 Model Evaluation Metrics (Dynamic View)")
    st.markdown("Bảng phân tích mức độ chính xác và hiệu năng từ dữ liệu mà AI đã phân tích trên hệ thống lúc này.")
    
    logs = st.session_state.eval_logs
    if not logs:
        st.warning("Bạn chưa chạy AI Pipeline hoặc chưa duyệt thông báo nào qua cổng Giáo Viên. Vui lòng thử demo xử lý rồi quay lại.")
        return
        
    df_logs = pd.DataFrame(logs)
    
    total_processed = len(df_logs)
    avg_latency = df_logs["latency"].mean()
    fallback_rate = (df_logs["fallback_used"].sum() / total_processed) * 100
    avg_confidence = (df_logs["confidence"].mean()) * 100
    
    st.subheader("1. Tổng quan hiệu năng (Real-time)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Số thông báo đã xử lý", f"{total_processed}")
    col2.metric("Thời gian/thông báo", f"{avg_latency:.2f}s")
    col3.metric("Fallback Mock", f"{fallback_rate:.1f}%")
    col4.metric("Avg Confidence", f"{avg_confidence:.1f}%")
    
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("2. Phân phối Ưu tiên (AI Labeled)")
        priority_counts = df_logs["priority_level"].value_counts().reset_index()
        priority_counts.columns = ["Priority Level", "Count"]
        
        # Dùng Bar chart
        fig_prior = px.pie(priority_counts, names="Priority Level", values="Count", title="Tỉ lệ nhãn được gắn")
        fig_prior.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0")
        st.plotly_chart(fig_prior, use_container_width=True)
    
    with col_b:
        st.subheader("3. Thời gian phản hồi (Latency Trend)")
        df_logs["Index"] = df_logs.index + 1
        fig_trend = px.line(df_logs, x="Index", y="latency", markers=True, title="Độ trễ xử lý (giây) trên các request")
        fig_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0")
        st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("### Dữ liệu nguyên thủy (Logs Trace)")
    st.dataframe(df_logs, use_container_width=True)

# Main App Navigation
st.sidebar.title("App Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Teacher Portal (Push)", "AI Processing Workflow", "Analytics", "Evaluation Metrics"])

if page == "Dashboard":
    page_dashboard()
elif page == "Teacher Portal (Push)":
    page_teacher_portal()
elif page == "AI Processing Workflow":
    page_ai_processing()
elif page == "Analytics":
    page_analytics()
elif page == "Evaluation Metrics":
    page_evaluation()
