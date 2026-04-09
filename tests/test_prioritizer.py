from nodes import prioritizer
from utils import llm_providers


def test_high_keyword_guardrail_without_llm(monkeypatch):
    def should_not_be_called(_: str, __: str):
        raise AssertionError("LLM chain should not be called for HIGH keyword guardrail")

    monkeypatch.setattr(prioritizer, "classify_with_provider_chain", should_not_be_called)
    state = {"teacher_note": "Thong bao han chot dong hoc phi den ngay mai"}

    result = prioritizer.prioritize_notification(state)

    assert result["priority_level"] == "High"
    assert result["priority_source"] == "keyword_guardrail"
    assert result["priority_confidence"] >= 0.9


def test_happy_path_llm_medium(monkeypatch):
    def fake_llm(_: str, __: str):
        return {
            "priority": "MEDIUM",
            "confidence": 0.88,
            "reason": "Parent meeting needs preparation",
            "provider": "openai",
            "model": "gpt-4o-mini",
        }

    monkeypatch.setattr(prioritizer, "classify_with_provider_chain", fake_llm)
    state = {"teacher_note": "Thong bao lich hop phu huynh cuoi ky"}

    result = prioritizer.prioritize_notification(state)

    assert result["priority_level"] == "Medium"
    assert result["priority_source"] == "llm"
    assert result["priority_provider"] == "openai"


def test_failure_path_llm_error_fallback_to_medium_keyword(monkeypatch):
    def failing_llm(_: str, __: str):
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(prioritizer, "classify_with_provider_chain", failing_llm)
    state = {"teacher_note": "Hop phu huynh vao thu Bay"}

    result = prioritizer.prioritize_notification(state)

    assert result["priority_level"] == "Medium"
    assert result["priority_source"] == "keyword_fallback"
    assert "quota exceeded" in result["priority_error"]


def test_failure_path_empty_text_returns_low():
    result = prioritizer.prioritize_notification({})

    assert result["priority_level"] == "Low"
    assert result["priority_source"] == "default"


def test_medium_keyword_override_when_llm_low_confidence(monkeypatch):
    def fake_llm(_: str, __: str):
        return {
            "priority": "LOW",
            "confidence": 0.60,
            "reason": "Likely informational",
            "provider": "openai",
            "model": "gpt-4o-mini",
        }

    monkeypatch.setattr(prioritizer, "classify_with_provider_chain", fake_llm)
    state = {"teacher_note": "Thong bao ngoai khoa can dang ky"}

    result = prioritizer.prioritize_notification(state)

    assert result["priority_level"] == "Medium"
    assert result["priority_source"] == "keyword_override"


def test_provider_failover_openai_to_anthropic(monkeypatch):
    monkeypatch.setenv("PRIORITIZER_PROVIDER_ORDER", "openai,anthropic")

    def openai_fail(_: str, __: str):
        raise RuntimeError("openai insufficient_quota")

    def anthropic_ok(_: str, __: str):
        return {
            "priority": "LOW",
            "confidence": 0.76,
            "reason": "General update",
            "provider": "anthropic",
            "model": "claude-3-5-haiku-latest",
        }

    monkeypatch.setattr(llm_providers, "classify_openai", openai_fail)
    monkeypatch.setattr(llm_providers, "classify_anthropic", anthropic_ok)

    result = llm_providers.classify_with_provider_chain("Ban tin tuan", "PROMPT")
    assert result["provider"] == "anthropic"


def test_provider_failover_openrouter_when_openai_fails(monkeypatch):
    monkeypatch.setenv("PRIORITIZER_PROVIDER_ORDER", "openai,openrouter")

    def openai_fail(_: str, __: str):
        raise RuntimeError("openai rate_limit")

    def openrouter_ok(_: str, __: str):
        return {
            "priority": "MEDIUM",
            "confidence": 0.82,
            "reason": "Meeting reminder",
            "provider": "openrouter",
            "model": "openai/gpt-4o-mini",
        }

    monkeypatch.setattr(llm_providers, "classify_openai", openai_fail)
    monkeypatch.setattr(llm_providers, "classify_openrouter", openrouter_ok)

    result = llm_providers.classify_with_provider_chain("Thong bao hop phu huynh", "PROMPT")
    assert result["provider"] == "openrouter"


def test_load_system_prompt_from_file(tmp_path, monkeypatch):
    from nodes import prioritizer

    prompt_file = tmp_path / "prioritizer_system_prompt.md"
    prompt_file.write_text("PROMPT_FROM_MD", encoding="utf-8")
    monkeypatch.setattr(prioritizer, "DEFAULT_PROMPT_DIR", tmp_path)
    monkeypatch.setattr(
        prioritizer,
        "classify_with_provider_chain",
        lambda _text, prompt: {
            "priority": "LOW",
            "confidence": 0.7,
            "reason": prompt,
            "provider": "mock",
            "model": "mock",
        },
    )

    result = prioritizer.prioritize_notification({"teacher_note": "Ban tin thong thuong"})
    assert result["priority_reason"] == "PROMPT_FROM_MD"


def test_load_system_prompt_fallback_to_txt(tmp_path, monkeypatch):
    from nodes import prioritizer

    txt_file = tmp_path / "prioritizer_system_prompt.txt"
    txt_file.write_text("PROMPT_FROM_TXT", encoding="utf-8")

    monkeypatch.setattr(prioritizer, "DEFAULT_PROMPT_DIR", tmp_path)
    monkeypatch.setattr(
        prioritizer,
        "classify_with_provider_chain",
        lambda _text, prompt: {
            "priority": "LOW",
            "confidence": 0.7,
            "reason": prompt,
            "provider": "mock",
            "model": "mock",
        },
    )

    result = prioritizer.prioritize_notification({"teacher_note": "Ban tin thong thuong"})
    assert result["priority_reason"] == "PROMPT_FROM_TXT"


def test_load_system_prompt_env_override(tmp_path, monkeypatch):
    from nodes import prioritizer

    override_file = tmp_path / "custom_prompt.md"
    override_file.write_text("PROMPT_FROM_ENV", encoding="utf-8")
    monkeypatch.setenv("PRIORITIZER_SYSTEM_PROMPT_FILE", str(override_file))
    monkeypatch.setattr(
        prioritizer,
        "classify_with_provider_chain",
        lambda _text, prompt: {
            "priority": "LOW",
            "confidence": 0.7,
            "reason": prompt,
            "provider": "mock",
            "model": "mock",
        },
    )

    result = prioritizer.prioritize_notification({"teacher_note": "Ban tin thong thuong"})
    assert result["priority_reason"] == "PROMPT_FROM_ENV"


def test_utils_load_prompt_multiple_prompt_names(tmp_path):
    from utils.prompt_loader import load_prompt

    p1 = tmp_path / "prioritizer_system_prompt.md"
    p2 = tmp_path / "summarizer_system_prompt.md"
    p1.write_text("PROMPT_PRIORITIZER", encoding="utf-8")
    p2.write_text("PROMPT_SUMMARIZER", encoding="utf-8")

    assert (
        load_prompt("prioritizer_system_prompt", prompt_dir=tmp_path)
        == "PROMPT_PRIORITIZER"
    )
    assert (
        load_prompt("summarizer_system_prompt", prompt_dir=tmp_path)
        == "PROMPT_SUMMARIZER"
    )
