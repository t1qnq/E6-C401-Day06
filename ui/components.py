import streamlit as st

def get_priority_color(level):
    level = (level or "").strip().lower()
    if level == "high":
        return "red", "#FF4B4B", "🔴"
    elif level == "medium":
        return "orange", "#FFA726", "🟡"
    elif level == "low":
        return "green", "#66BB6A", "🟢"
    return "gray", "#BDBDBD", "⚪"

def render_priority_badge(level):
    if not level:
        level = "Unclassified"
    
    color_name, hex_color, icon = get_priority_color(level)
    level_class = f"badge-{level.lower()}" if level.lower() in ["high", "medium", "low"] else "badge-low"
    
    html = f"""
    <span class="badge {level_class}">
        {icon} {level.upper()}
    </span>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_notification_card(notif, container=None):
    use_container = container or st
    
    with use_container.container():
        st.markdown('<div class="notif-card">', unsafe_allow_html=True)
        
        # Header row
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {notif.get('title', 'Unknown Title')}")
            st.caption(f"Sender: {notif.get('sender', 'Unknown')} | {notif.get('timestamp', '')[:10]}")
        with col2:
            priority = notif.get('_priority', '')
            if priority:
                render_priority_badge(priority)
            
            st.caption(f"Trọng tâm: {notif.get('category', 'Khác').upper()}")
        
        # Details
        scope = notif.get('receiver_scope', '')
        st.markdown(f"**Phạm vi:** `{scope}`")
        
        # Summarized text or original
        content = notif.get('content', '')
        summary = notif.get('_brief_summary')
        
        if summary:
            st.markdown("**Tóm tắt nhanh:**")
            st.info(summary)
        else:
            # Show a truncated content if no summary yet
            st.markdown(f"{content[:150]}..." if len(content) > 150 else content)
            
        st.markdown('</div>', unsafe_allow_html=True)

def render_timeline_step(node_name, status="success", description="", result_data=None):
    """
    Render a step in the AI pipeline timeline.
    status: 'success', 'processing', 'error'
    """
    icon = "✓" if status == "success" else ("⚙" if status == "processing" else "✗")
    icon_cls = "success" if status == "success" else ("processing" if status == "processing" else "error")
    
    html = f"""
    <div class="timeline-step">
        <div class="timeline-icon {icon_cls}">{icon}</div>
        <div class="timeline-content">
            <div class="timeline-title">{node_name}</div>
            <div class="timeline-desc">{description}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    if result_data:
        st.json(result_data, expanded=False)

def render_explainability_panel(explain_dict):
    if not explain_dict:
        return
        
    with st.expander("🔍 Chi tiết phân loại ưu tiên", expanded=False):
        st.markdown(f"**Lý do:** {explain_dict.get('summary', 'Unknown')}")
        st.markdown(f"**Nguồn quyết định:** `{explain_dict.get('source', 'Unknown')}`")
        
        evidence = explain_dict.get('evidence', [])
        if evidence:
            st.markdown("**Bằng chứng:**")
            for item in evidence:
                st.markdown(f"- {item}")

def render_feedback_buttons(notif_id):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👍 Đồng ý", key=f"up_{notif_id}"):
            st.success("Đã ghi nhận phản hồi đồng tình.")
            return "upvote"
    with col2:
        if st.button("👎 Phản đối", key=f"down_{notif_id}"):
            st.warning("Đã ghi nhận phản hồi. Cảm ơn đống góp.")
            return "downvote"
    with col3:
        pass # Placeholder for custom editing, which could trigger a form

    return None
