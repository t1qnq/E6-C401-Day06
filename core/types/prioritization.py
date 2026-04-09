from typing import Literal, NotRequired, TypedDict

PriorityValue = Literal["HIGH", "MEDIUM", "LOW"]


class LlmClassification(TypedDict):
    priority: PriorityValue
    confidence: float
    reason: str
    provider: str
    model: str


class ExplainabilityPayload(TypedDict):
    summary: str
    source: str
    evidence: list[str]


class PrioritizationResult(TypedDict):
    priority_level: str
    priority_confidence: float
    priority_reason: str
    priority_source: str
    priority_provider: NotRequired[str]
    priority_model: NotRequired[str]
    priority_error: NotRequired[str]
    priority_explainability: NotRequired[ExplainabilityPayload]
