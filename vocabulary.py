"""
vocabulary.py — Single source of truth for all frozen labels and mappings.

This file is locked after March 30, 2026. Do not rename or add values
without agreement from both team members.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Team metadata
# ---------------------------------------------------------------------------
TEAM_NAME = "Hackstreet Boys"
TEAM_MEMBERS = ["Roopal Guha Neogi", "Suyash Kumar"]
ENV_NAME = "it_helpdesk_ticket_routing"
ENV_NAME_FULL = "it_helpdesk_ticket_routing_openenv"

# ---------------------------------------------------------------------------
# Frozen label sets
# ---------------------------------------------------------------------------
ISSUE_TYPES: list[str] = [
    "billing_license",
    "identity_access",
    "application_support",
    "service_request",
    "spam_phishing",
    "general_inquiry",
    "security_compliance",
    "onboarding",
    "feature_request",
]

PRIORITIES: list[str] = [
    "critical",
    "high",
    "medium",
    "low",
]

ASSIGNMENT_GROUPS: list[str] = [
    "license_ops",
    "service_desk",
    "application_team",
    "procurement",
    "security_team",
    "onboarding_ops",
]

RESOLUTION_ACTIONS: list[str] = [
    "fulfill",
    "escalate",
    "assign",
    "ignore",
    "acknowledge",
]

# ---------------------------------------------------------------------------
# Deterministic routing maps (used by heuristic inference and grader)
# ---------------------------------------------------------------------------
ISSUE_TYPE_TO_GROUP: dict[str, str] = {
    "billing_license":    "license_ops",
    "identity_access":    "service_desk",
    "application_support":"application_team",
    "service_request":    "procurement",
    "spam_phishing":      "security_team",
    "general_inquiry":    "service_desk",
    "security_compliance":"security_team",
    "onboarding":         "onboarding_ops",
    "feature_request":    "application_team",
}

ISSUE_TYPE_TO_ACTION: dict[str, str] = {
    "billing_license":    "fulfill",
    "identity_access":    "fulfill",
    "application_support":"escalate",
    "service_request":    "assign",
    "spam_phishing":      "ignore",
    "general_inquiry":    "acknowledge",
    "security_compliance":"escalate",
    "onboarding":         "fulfill",
    "feature_request":    "acknowledge",
}

# ---------------------------------------------------------------------------
# Priority adjacency (for partial-credit scoring)
# ---------------------------------------------------------------------------
PRIORITY_ORDER: dict[str, int] = {
    "critical": 3,
    "high":     2,
    "medium":   1,
    "low":      0,
}

# ---------------------------------------------------------------------------
# Near-miss issue type pairs (for partial-credit scoring)
# ---------------------------------------------------------------------------
NEAR_MISS_PAIRS: list[tuple[str, str]] = [
    ("billing_license",    "service_request"),
    ("identity_access",    "security_compliance"),
    ("application_support","service_request"),
    ("spam_phishing",      "security_compliance"),
    ("general_inquiry",    "service_request"),
    ("onboarding",         "identity_access"),
]
