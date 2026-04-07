from __future__ import annotations

from models import HelpdeskTicketAction, HelpdeskTicketRecord

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

ASSIGNMENT_GROUP_SIMILARITY = {
    ("procurement", "license_ops"): 0.55,
    ("license_ops", "procurement"): 0.55,
    ("service_desk", "onboarding_ops"): 0.5,
    ("onboarding_ops", "service_desk"): 0.5,
    ("application_team", "security_team"): 0.35,
    ("security_team", "application_team"): 0.35,
    ("service_desk", "application_team"): 0.25,
    ("application_team", "service_desk"): 0.25,
    ("service_desk", "security_team"): 0.2,
    ("security_team", "service_desk"): 0.2,
}

RESOLUTION_ACTION_SIMILARITY = {
    ("assign", "escalate"): 0.6,
    ("escalate", "assign"): 0.6,
    ("acknowledge", "fulfill"): 0.35,
    ("fulfill", "acknowledge"): 0.35,
    ("assign", "fulfill"): 0.25,
    ("fulfill", "assign"): 0.25,
    ("escalate", "fulfill"): 0.2,
    ("fulfill", "escalate"): 0.2,
    ("acknowledge", "assign"): 0.2,
    ("assign", "acknowledge"): 0.2,
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


def _score_exact_or_table(
    predicted: str | None,
    expected: str,
    similarity_table: dict[tuple[str, str], float],
) -> float:
    pred = _normalized(predicted)
    exp = _normalized(expected)
    if not pred:
        return 0.0
    if pred == exp:
        return 1.0
    return similarity_table.get((pred, exp), 0.0)


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


def _score_route(
    action: HelpdeskTicketAction,
    *,
    issue_type: str,
    priority: str,
    assignment_group: str,
    resolution_action: str,
    score_multiplier: float,
    task_id: int,
) -> tuple[float, dict[str, float]]:
    field_scores = {
        "issue_type": _score_exact_or_similar(action.issue_type, issue_type),
        "priority": _score_priority(action.priority, priority),
        "assignment_group": _score_exact_or_table(
            action.assignment_group,
            assignment_group,
            ASSIGNMENT_GROUP_SIMILARITY,
        ),
        "resolution_action": _score_exact_or_table(
            action.resolution_action,
            resolution_action,
            RESOLUTION_ACTION_SIMILARITY,
        ),
    }
    if score_multiplier != 1.0:
        field_scores = {
            field: round(score * score_multiplier, 4)
            for field, score in field_scores.items()
        }
    weights = TASK_WEIGHTS[task_id]
    raw_score = sum(field_scores[field] * weight for field, weight in weights.items())
    return raw_score, field_scores


def _alternate_route_available(ticket: HelpdeskTicketRecord) -> bool:
    return any(
        value is not None
        for value in (
            ticket.alternate_issue_type,
            ticket.alternate_priority,
            ticket.alternate_assignment_group,
            ticket.alternate_resolution_action,
        )
    ) and ticket.alternate_route_score_multiplier > 0.0


def grade_action(
    action: HelpdeskTicketAction,
    ticket: HelpdeskTicketRecord,
    task_id: int,
) -> tuple[float, dict[str, float]]:
    if task_id not in TASK_WEIGHTS:
        raise ValueError(f"Unsupported task_id: {task_id}")

    primary_score, primary_field_scores = _score_route(
        action,
        issue_type=ticket.issue_type,
        priority=ticket.priority,
        assignment_group=ticket.assignment_group,
        resolution_action=ticket.resolution_action,
        score_multiplier=1.0,
        task_id=task_id,
    )
    chosen_score = primary_score
    chosen_field_scores = primary_field_scores

    if _alternate_route_available(ticket):
        alternate_score, alternate_field_scores = _score_route(
            action,
            issue_type=ticket.alternate_issue_type or ticket.issue_type,
            priority=ticket.alternate_priority or ticket.priority,
            assignment_group=(
                ticket.alternate_assignment_group or ticket.assignment_group
            ),
            resolution_action=(
                ticket.alternate_resolution_action or ticket.resolution_action
            ),
            score_multiplier=ticket.alternate_route_score_multiplier,
            task_id=task_id,
        )
        if alternate_score > chosen_score:
            chosen_score = alternate_score
            chosen_field_scores = alternate_field_scores

    score = max(0.0, min(1.0, chosen_score))
    breakdown = {field: chosen_field_scores[field] for field in TASK_WEIGHTS[task_id]}
    return score, breakdown
