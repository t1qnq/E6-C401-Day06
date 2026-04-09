import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        /* Base styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        /* Dark theme specifics */
        .stApp {
            background-color: #0E1117;
        }

        /* Glassmorphism Cards */
        .notif-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .notif-card:hover {
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* Priority Badges */
        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            display: inline-block;
        }

        .badge-high {
            background-color: rgba(255, 75, 75, 0.2);
            color: #FF4B4B;
            border: 1px solid rgba(255, 75, 75, 0.5);
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.2);
        }

        .badge-medium {
            background-color: rgba(255, 167, 38, 0.2);
            color: #FFA726;
            border: 1px solid rgba(255, 167, 38, 0.5);
        }

        .badge-low {
            background-color: rgba(102, 187, 106, 0.2);
            color: #66BB6A;
            border: 1px solid rgba(102, 187, 106, 0.5);
        }

        /* Timeline styles */
        .timeline-step {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1rem;
            position: relative;
        }
        
        .timeline-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            background: #2b313e;
            z-index: 2;
        }

        .timeline-icon.success {
            background: rgba(102, 187, 106, 0.2);
            color: #66BB6A;
        }

        .timeline-icon.processing {
            background: rgba(255, 167, 38, 0.2);
            color: #FFA726;
        }

        .timeline-content {
            flex-grow: 1;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 8px;
        }

        .timeline-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: #E2E8F0;
        }
        
        .timeline-desc {
            font-size: 0.875rem;
            color: #94A3B8;
        }
        </style>
    """, unsafe_allow_html=True)
