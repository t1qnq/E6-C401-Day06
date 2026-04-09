"""Constants for notification prioritization."""

HIGH_KEYWORDS = {
    "hoc phi",
    "dong phi",
    "nop phi",
    "tai chinh",
    "han chot",
    "deadline",
    "khan",
    "khan cap",
    "urgent",
    "qua han",
}

MEDIUM_KEYWORDS = {
    "hop",
    "hop phu huynh",
    "ngoai khoa",
    "su kien",
    "dang ky",
    "event",
    "workshop",
    "tham gia",
}

LOW_KEYWORDS = {
    "ban tin",
    "thong bao chung",
    "cap nhat",
    "nhac nho",
}

PRIORITY_TITLE_CASE = {
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
}

DEFAULT_SYSTEM_PROMPT = """
You are an assistant for Vinschool parent notifications.
Classify priority into one of: HIGH, MEDIUM, LOW.

Rules:
- HIGH: urgent deadlines, tuition/finance deadlines, emergency meeting, health/safety issues.
- MEDIUM: regular meetings, extracurricular preparation, activities that need action soon.
- LOW: informational updates, newsletters, non-urgent announcements.

Return strict JSON only:
{"priority":"HIGH|MEDIUM|LOW","confidence":0.0-1.0,"reason":"short reason"}
""".strip()
