from __future__ import annotations

TEAM_NAME = "Hackstreet Boys"
TEAM_MEMBERS = ("Roopal Guha Neogi", "Suyash Kumar")

PROJECT_TITLE = "IT Helpdesk Ticket Routing OpenEnv"
DOMAIN_NAME = "IT Helpdesk Ticket Routing"

OPENENV_NAME = "it_helpdesk_ticket_routing_openenv"
APP_ENV_NAME = "it_helpdesk_ticket_routing"

ISSUE_TYPES = (
    "billing_license",
    "identity_access",
    "application_support",
    "service_request",
    "spam_phishing",
    "general_inquiry",
    "security_compliance",
    "onboarding",
    "feature_request",
)

PRIORITIES = ("critical", "high", "medium", "low")

ASSIGNMENT_GROUPS = (
    "license_ops",
    "service_desk",
    "application_team",
    "procurement",
    "security_team",
    "onboarding_ops",
)

RESOLUTION_ACTIONS = (
    "fulfill",
    "escalate",
    "assign",
    "ignore",
    "acknowledge",
)

TASK_IDS = (1, 2, 3)

ISSUE_TYPE_TO_ASSIGNMENT_GROUP = {
    "billing_license": "license_ops",
    "identity_access": "service_desk",
    "application_support": "application_team",
    "service_request": "procurement",
    "spam_phishing": "security_team",
    "general_inquiry": "service_desk",
    "security_compliance": "security_team",
    "onboarding": "onboarding_ops",
    "feature_request": "application_team",
}

ISSUE_TYPE_TO_RESOLUTION_ACTION = {
    "billing_license": "fulfill",
    "identity_access": "fulfill",
    "application_support": "escalate",
    "service_request": "assign",
    "spam_phishing": "ignore",
    "general_inquiry": "acknowledge",
    "security_compliance": "escalate",
    "onboarding": "fulfill",
    "feature_request": "acknowledge",
}
