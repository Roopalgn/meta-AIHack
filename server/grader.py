from __future__ import annotations

from models import HelpdeskTicketAction, HelpdeskTicketRecord

TASK_SCORE_EPSILON = 0.01


ISSUE_TYPE_SIMILARITY = {
    ("billing_license", "service_request"): 0.4,
    ("service_request", "billing_license"): 0.4,
    ("application_support", "identity_access"): 0.5,
    ("identity_access", "application_support"): 0.5,
    ("application_support", "feature_request"): 0.35,
    ("feature_request", "application_support"): 0.35,
    ("onboarding", "identity_access"): 0.4,
    ("identity_access", "onboarding"): 0.4,
    ("general_inquiry", "feature_request"): 0.3,
    ("feature_request", "general_inquiry"): 0.3,
    ("general_inquiry", "service_request"): 0.25,
    ("service_request", "general_inquiry"): 0.25,
    ("spam_phishing", "security_compliance"): 0.4,
    ("security_compliance", "spam_phishing"): 0.4,
    ("security_compliance", "billing_license"): 0.2,
    ("billing_license", "security_compliance"): 0.2,
}

PRIORITY_SCORES = {
    ("critical", "high"): 0.6,
    ("high", "critical"): 0.6,
    ("high", "medium"): 0.5,
    ("medium", "high"): 0.5,
    ("medium", "low"): 0.4,
    ("low", "medium"): 0.4,
    ("critical", "medium"): 0.3,
    ("medium", "critical"): 0.3,
    ("critical", "low"): 0.1,
    ("low", "critical"): 0.1,
    ("high", "low"): 0.2,
    ("low", "high"): 0.2,
}


TASK_WEIGHTS = {
    1: {"issue_type": 1.0},
    2: {"issue_type": 0.6, "priority": 0.4},
    3: {
        "issue_type": 0.35,
        "priority": 0.20,
        "assignment_group": 0.25,
        "resolution_action": 0.20,
    },
}


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower()


def _score_exact_or_similar(predicted: str | None, expected: str) -> float:
    pred = _normalized(predicted)
    exp = _normalized(expected)
    if not pred:
        return 0.0
    if pred == exp:
        return 1.0
    return ISSUE_TYPE_SIMILARITY.get((pred, exp), 0.0)


def _score_priority(predicted: str | None, expected: str) -> float:
    pred = _normalized(predicted)
    exp = _normalized(expected)
    if not pred:
        return 0.0
    if pred == exp:
        return 1.0
    return PRIORITY_SCORES.get((pred, exp), 0.0)


def _score_exact(predicted: str | None, expected: str) -> float:
    return 1.0 if _normalized(predicted) == _normalized(expected) and predicted else 0.0


def grade_action(
    action: HelpdeskTicketAction,
    ticket: HelpdeskTicketRecord,
    task_id: int,
) -> tuple[float, dict[str, float]]:
    if task_id not in TASK_WEIGHTS:
        raise ValueError(f"Unsupported task_id: {task_id}")

    field_scores = {
        "issue_type": _score_exact_or_similar(action.issue_type, ticket.issue_type),
        "priority": _score_priority(action.priority, ticket.priority),
        "assignment_group": _score_exact(
            action.assignment_group, ticket.assignment_group
        ),
        "resolution_action": _score_exact(
            action.resolution_action, ticket.resolution_action
        ),
    }

    weights = TASK_WEIGHTS[task_id]
    raw_score = sum(field_scores[field] * weight for field, weight in weights.items())
    score = max(TASK_SCORE_EPSILON, min(1.0 - TASK_SCORE_EPSILON, raw_score))
    breakdown = {field: field_scores[field] for field in weights}
    return score, breakdown
