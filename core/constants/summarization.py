"""Constants for notification summarization."""

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
