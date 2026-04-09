import json
from pathlib import Path
import streamlit as st

DATA_PATH = Path("api/data/mock_data.json")

@st.cache_data
def load_data():
    """Load mock data and cache it in Streamlit."""
    if not DATA_PATH.exists():
        return {"students": [], "notifications": []}
    
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"students": [], "notifications": []}

def get_notifications():
    """Retrieve all notifications."""
    data = load_data()
    return data.get("notifications", [])

def get_students():
    """Retrieve all students."""
    data = load_data()
    return data.get("students", [])

def get_student_for_notification(notif):
    """Find student profile based on receiver_ids."""
    receiver_ids = notif.get("receiver_ids", [])
    if not receiver_ids:
        return {}
    
    # We just try to find the first matching student ID for simplicity in individual scopes
    target_id = receiver_ids[0]
    for student in get_students():
        if student.get("student_id") == target_id:
            return student
    
    return {}

def get_analytics():
    """Aggregate stats for analytics page."""
    notifications = get_notifications()
    
    total = len(notifications)
    
    categories = {}
    scopes = {}
    
    for n in notifications:
        cat = n.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        
        scope = n.get("receiver_scope", "unknown")
        scopes[scope] = scopes.get(scope, 0) + 1
        
    return {
        "total_notifications": total,
        "categories": categories,
        "scopes": scopes
    }
