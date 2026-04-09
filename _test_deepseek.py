from dotenv import load_dotenv
load_dotenv()

from utils.llm_providers import classify_deepseek

result = classify_deepseek(
    "Thong bao khan: Hoc sinh lop 3A bi sot cao, xin nghi hoc ngay 20/5",
    'You classify school notifications as HIGH, MEDIUM, or LOW priority. Reply in JSON: {"priority": "...", "confidence": 0.0-1.0, "reason": "..."}'
)
print("=== DEEPSEEK RESULT ===")
print(result)
