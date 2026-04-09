from typing import Any, Dict

from services.prioritization.feedback_learning import feedback_learner


def _normalize_priority(value: str) -> str:
	val = (value or "").strip().upper()
	return val if val in {"HIGH", "MEDIUM", "LOW"} else ""


def handle_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
	"""Handle parent feedback and feed learning signals for periodic keyword updates."""
	action = str(state.get("feedback_action", "")).lower().strip()
	corrected_priority = _normalize_priority(str(state.get("corrected_priority", "")))
	original_priority = _normalize_priority(str(state.get("priority_level", "")))

	text_parts = []
	for key in ("teacher_note", "extracted_text"):
		value = state.get(key)
		if isinstance(value, str) and value.strip():
			text_parts.append(value.strip())

	notification = state.get("notification")
	if isinstance(notification, dict):
		for key in ("title", "content"):
			value = notification.get(key)
			if isinstance(value, str) and value.strip():
				text_parts.append(value.strip())

	text = "\n".join(text_parts)

	if action in {"upvote", "downvote", "correct"} and corrected_priority:
		feedback_learner.append_feedback_signal(
			{
				"action": action,
				"original_priority": original_priority,
				"corrected_priority": corrected_priority,
				"text": text,
				"category": notification.get("category") if isinstance(notification, dict) else None,
				"receiver_scope": notification.get("receiver_scope") if isinstance(notification, dict) else None,
			}
		)
		feedback_learner.maybe_rebuild()

		return {
			"feedback_recorded": True,
			"learning_signal": f"feedback={action}; from={original_priority}; to={corrected_priority}",
		}

	return {"feedback_recorded": False, "learning_signal": "no_valid_feedback"}
