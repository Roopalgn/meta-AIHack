#!/usr/bin/env python3
"""
Inference script for the IT Helpdesk Ticket Routing OpenEnv environment.

Uses the competition-mandated environment variables:
  API_BASE_URL  - LLM provider base URL
  MODEL_NAME    - model identifier
  HF_TOKEN      - authentication token

Can run against a local server (default http://localhost:8000) or a
remote HuggingFace Space URL passed via ENV_URL.

Uses the WebSocket-based EnvClient for multi-step episodes.
"""
from __future__ import annotations

import json
import os

import httpx
from openai import OpenAI

from client import HelpdeskTicketEnvClient
from models import HelpdeskTicketAction

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")

SEED = 42
TASKS = [1, 2, 3]

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

llm_client: OpenAI | None = None

if MODEL_NAME and HF_TOKEN:
    llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


SYSTEM_PROMPT = """\
You are an expert IT helpdesk ticket routing agent. Given a helpdesk ticket, you must produce a JSON object with the requested fields.

Valid values:
- issue_type: billing_license, identity_access, application_support, service_request, spam_phishing, general_inquiry, security_compliance, onboarding, feature_request
- priority: critical, high, medium, low
- assignment_group: license_ops, service_desk, application_team, procurement, security_team, onboarding_ops
- resolution_action: fulfill, escalate, assign, ignore, acknowledge

Return ONLY valid JSON with the requested fields. No markdown, no explanation."""


def call_llm(ticket: dict, allowed_fields: list[str], instructions: str) -> dict:
    assert llm_client is not None, "LLM client not configured"

    user_msg = (
        f"Instructions: {instructions}\n\n"
        f"Allowed fields: {', '.join(allowed_fields)}\n\n"
        f"Title: {ticket['title']}\n"
        f"Requester: {ticket['requester']}\n"
        f"Description: {ticket['description']}\n\n"
        f"Respond with JSON containing ONLY these fields: {', '.join(allowed_fields)}"
    )

    response = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=256,
    )

    text = response.choices[0].message.content or "{}"
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Heuristic fallback (no LLM needed)
# ---------------------------------------------------------------------------

KEYWORD_ISSUE_TYPES = {
    "invoice": "billing_license",
    "charge": "billing_license",
    "refund": "billing_license",
    "payment": "billing_license",
    "billing": "billing_license",
    "license": "billing_license",
    "sign in": "identity_access",
    "login": "identity_access",
    "password": "identity_access",
    "locked": "identity_access",
    "2fa": "identity_access",
    "sso": "identity_access",
    "bug": "application_support",
    "error": "application_support",
    "exception": "application_support",
    "crash": "application_support",
    "production": "application_support",
    "latency": "application_support",
    "timeout": "application_support",
    "webhook": "application_support",
    "migration": "application_support",
    "pricing": "service_request",
    "quote": "service_request",
    "demo": "service_request",
    "enterprise": "service_request",
    "rollout": "service_request",
    "sandbox": "service_request",
    "trial": "service_request",
    "seat": "service_request",
    "seats": "service_request",
    "spam": "spam_phishing",
    "click now": "spam_phishing",
    "guaranteed": "spam_phishing",
    "unsubscribe": "spam_phishing",
    "phishing": "spam_phishing",
    "compromised": "spam_phishing",
    "compliance": "security_compliance",
    "regulation": "security_compliance",
    "gdpr": "security_compliance",
    "audit": "security_compliance",
    "pentest": "security_compliance",
    "vulnerabilities": "security_compliance",
    "security policy": "security_compliance",
    "onboarding": "onboarding",
    "welcome": "onboarding",
    "getting started": "onboarding",
    "new hire": "onboarding",
    "contractor": "onboarding",
    "feedback": "feature_request",
    "suggestion": "feature_request",
    "improve": "feature_request",
    "roadmap": "feature_request",
    "export": "feature_request",
}

ISSUE_TYPE_TO_GROUP = {
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

ISSUE_TYPE_TO_ACTION = {
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


def heuristic_action(ticket: dict, allowed_fields: list[str]) -> dict:
    text = (ticket.get("title", "") + " " + ticket.get("description", "")).lower()

    issue_type = "general_inquiry"
    for kw, mapped_issue_type in KEYWORD_ISSUE_TYPES.items():
        if kw in text:
            issue_type = mapped_issue_type
            break

    priority = "medium"
    if any(w in text for w in ["urgent", "critical", "blocking", "asap", "immediately"]):
        priority = "critical"
    elif any(w in text for w in ["important", "high priority", "revenue"]):
        priority = "high"
    elif any(w in text for w in ["low", "whenever", "no rush"]):
        priority = "low"

    result: dict = {}
    if "issue_type" in allowed_fields:
        result["issue_type"] = issue_type
    if "priority" in allowed_fields:
        result["priority"] = priority
    if "assignment_group" in allowed_fields:
        result["assignment_group"] = ISSUE_TYPE_TO_GROUP.get(issue_type, "service_desk")
    if "resolution_action" in allowed_fields:
        result["resolution_action"] = ISSUE_TYPE_TO_ACTION.get(issue_type, "acknowledge")
    return result


# ---------------------------------------------------------------------------
# Main loop using WebSocket client for multi-step episodes
# ---------------------------------------------------------------------------

def run():
    # Quick HTTP health check
    http = httpx.Client(base_url=ENV_URL, timeout=30.0)
    health = http.get("/health")
    health.raise_for_status()
    print(f"Connected to {ENV_URL}: {health.json()}")

    tasks_resp = http.get("/tasks")
    tasks_resp.raise_for_status()
    available_tasks = {t["id"]: t for t in tasks_resp.json()["tasks"]}
    print(f"Available tasks: {[t['name'] for t in available_tasks.values()]}")
    http.close()

    all_scores: dict[int, list[float]] = {}

    for task_id in TASKS:
        if task_id not in available_tasks:
            print(f"Task {task_id} not available, skipping")
            continue

        task = available_tasks[task_id]
        print(f"\n--- Task {task_id}: {task['name']} ({task['difficulty']}) ---")

        # Use sync WebSocket client for multi-step episode
        sync_client = HelpdeskTicketEnvClient(base_url=ENV_URL).sync()
        with sync_client:
            result = sync_client.reset(seed=SEED, task_id=task_id)
            obs = result.observation

            task_scores: list[float] = []
            step_num = 0

            while not result.done:
                ticket = obs.current_ticket
                if ticket is None:
                    break

                allowed = obs.allowed_fields
                instructions = obs.instructions

                if llm_client is not None:
                    action_dict = call_llm(ticket, allowed, instructions)
                else:
                    action_dict = heuristic_action(ticket, allowed)

                action = HelpdeskTicketAction(**action_dict)
                result = sync_client.step(action)
                obs = result.observation

                step_num += 1
                print(f"  Step {step_num}: reward={result.reward} done={result.done}")

                if result.reward is not None:
                    task_scores.append(result.reward)

        all_scores[task_id] = task_scores
        final = task_scores[-1] if task_scores else 0.0
        print(f"  Task {task_id} final reward: {final:.4f}")

    # Summary
    print("\n=== RESULTS ===")
    overall = []
    for tid in TASKS:
        if tid in all_scores:
            scores = all_scores[tid]
            avg = sum(scores) / len(scores) if scores else 0.0
            overall.append(avg)
            print(f"Task {tid}: avg_score={avg:.4f} ({len(scores)} steps)")
    if overall:
        print(f"Overall: {sum(overall) / len(overall):.4f}")


if __name__ == "__main__":
    run()
