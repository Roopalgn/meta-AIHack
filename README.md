---
title: IT Helpdesk Ticket Routing OpenEnv
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
  - helpdesk
  - ticket-routing
  - customer-support
---

# IT Helpdesk Ticket Routing OpenEnv

IT Helpdesk Ticket Routing is a deterministic OpenEnv environment for queue-based enterprise support operations. The agent sees one ticket at a time and must choose the correct issue type, priority, assignment group, and resolution action while handling investigation, clarification, deferral, incident management, and queue-level tradeoffs.

If you are comfortable reading intermediate Python projects, this repo should feel straightforward: start the server, reset an episode, step through ticket decisions, and inspect how the environment scores and evolves.

## Highlights

- real-world workflow: this models the kind of routing decisions human helpdesk teams actually make
- typed scoring: every final routing decision is deterministic and easy to grade
- meaningful difficulty ladder: all three tasks keep the same output contract while adding hidden context and queue pressure
- queue consequences: earlier decisions can change later tickets, capacity, incident coverage, and terminal reward
- reproducible baseline: `inference.py` runs deterministically and the repo includes a fixed-seed regression sweep

## Environment Overview

Each episode is a short ticket queue. The agent may:

- investigate hidden context with a small tool surface
- request clarification before committing
- defer a ticket and accept later queue consequences
- open an incident for risky tickets
- submit the final routing decision

The effective dataset currently contains 78 deterministic helpdesk records after loading the checked-in dataset plus curated queue-expansion records. Hard episodes can hide decisive routing context until the right tool is used and can generate downstream follow-up work when earlier handling is weak.

A typical episode looks like this: the environment shows one ticket, the agent can inspect or ask for more context if needed, then it either routes the ticket immediately or defers it and accepts the queue impact later in the episode.

## Task Ladder

| ID | Name | Difficulty | Required Fields | What Changes |
|----|------|------------|-----------------|--------------|
| 1 | Guided Full Routing | Easy | `issue_type`, `priority`, `assignment_group`, `resolution_action` | mostly visible single-ticket routing |
| 2 | Contextual Full Routing | Medium | `issue_type`, `priority`, `assignment_group`, `resolution_action` | partial observability, investigation, clarification, moderate queue carry-over |
| 3 | Adaptive Queue Routing | Hard | `issue_type`, `priority`, `assignment_group`, `resolution_action` | hidden context, queue pressure, deferrals, incident handling, clustered follow-ons |

## Action Space

| Action Type | Required Fields | Notes |
|-------------|-----------------|-------|
| `submit` | `issue_type`, `priority`, `assignment_group`, `resolution_action` | final routing answer for the current ticket |
| `investigate` | `tool_name`, optional `tool_target_ticket_id` | reveals hidden context when the right tool is used |
| `request_info` | none | asks for clarification on the current ticket |
| `open_incident` | none | reserves incident handling capacity before routing risky tickets |
| `defer` | none | pushes the ticket later in the queue and can create downstream penalties |

Locked submit vocabularies:

- `issue_type`: `billing_license`, `identity_access`, `application_support`, `service_request`, `spam_phishing`, `general_inquiry`, `security_compliance`, `onboarding`, `feature_request`
- `priority`: `critical`, `high`, `medium`, `low`
- `assignment_group`: `license_ops`, `service_desk`, `application_team`, `procurement`, `security_team`, `onboarding_ops`
- `resolution_action`: `fulfill`, `escalate`, `assign`, `ignore`, `acknowledge`

Available investigation tools:

- `lookup_related_ticket`
- `lookup_requester_history`
- `lookup_internal_routing_note`
- `lookup_queue_capacity_forecast`
- `lookup_queue_cluster_summary`

Invalid, partial, or schema-mismatched actions are handled through a deterministic penalty path.

## Observation And State Space

Each observation includes:

- task metadata: `task_id`, `task_name`, `instructions`
- routing contract: `allowed_fields`, `available_action_types`, `available_tools`
- current ticket fields such as `ticket_id`, `title`, `requester`, `description`, and optional extra context such as `ambiguity_note`, `planning_note`, `related_ticket_preview`, `capacity_state`, and `cluster_summary`
- queue progress: `queue_size`, `tickets_remaining`, `tickets_processed`, `queue_position`, `progress_fraction`
- feedback and reward telemetry: `reward`, `rubric_reward`, `last_reward_components`, `average_score_so_far`, `history`
- episode status: `done`

`state()` exposes the internal episode snapshot, including the current queue, cumulative reward, per-ticket scores, capacity counters, incident usage, planning penalties, queue-management metrics, and any follow-up events created by earlier decisions.

## Determinism And Scoring

- `reset(seed=..., task_id=...)` deterministically controls queue sampling and episode setup
- same seed + same action sequence => same queue order, rewards, and episode outcome
- both per-step `reward` and terminal `rubric_reward` stay in `[0.0, 1.0]`
- hard-task tickets may expose alternate acceptable routes with explicit score multipliers
- queue management matters: the final score blends routing quality with how well the episode was handled overall

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Run the server locally:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

Basic checks:

```bash
curl http://localhost:7860/health
curl http://localhost:7860/tasks
```

## Baseline Inference

### Heuristic mode

If no LLM credentials are set, the baseline uses deterministic local routing heuristics:

```bash
python inference.py
```

To target one task explicitly:

```bash
TASK_ID=3 python inference.py
```

### LLM mode

`inference.py` supports OpenAI-client execution with the required evaluator-style environment variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `API_KEY`
- `HF_TOKEN`

Then run:

```bash
python inference.py
```

Optional runtime variables:

- `ENV_URL` (default: `http://localhost:7860`)
- `SEED`
- `TASK_ID`
- `RUN_ALL_TASKS` (compatibility alias; all tasks already run by default when `TASK_ID` is unset)

### Reproducibility sweep

```bash
python scripts/baseline_repro_check.py --seeds 42-46 --task-ids 1,2,3 --expect-min 0.40 --expect-max 0.95
```

Example fixed-seed baseline snapshot from that command:

| Metric | Value |
|--------|-------|
| Task 1 average | `0.6866` |
| Task 2 average | `0.3206` |
| Task 3 average | `0.3259` |
| Overall average | `0.4444` |
| Observed min / max | `0.2162` / `0.8579` |

## Docker

Build:

```bash
docker build -t helpdesk-ticket-routing-root .
```

Run:

```bash
docker run -p 7860:7860 helpdesk-ticket-routing-root
```

Then point `inference.py` at the container with the default `ENV_URL` or an explicit override.

## API Surface

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | health check |
| POST | `/reset` | start a new episode |
| POST | `/step` | submit an action |
| GET | `/state` | inspect internal state |
| GET | `/tasks` | list task metadata |
| GET | `/web` | lightweight Hugging Face Space UI |
| GET | `/docs` | interactive API docs |
| GET | `/baseline` | deterministic baseline rollout helper |

## Repository Layout

```text
server/
  app.py
  environment.py
  grader.py
  reward.py
  tasks.py
  Dockerfile
data/
  dataset.json
models.py
client.py
inference.py
scripts/
  baseline_repro_check.py
openenv.yaml
pyproject.toml
requirements.txt
```

## Validation

The project includes the main checks you would expect for a reproducible environment:

- `openenv validate` passes
- the baseline reproducibility sweep passes on fixed seeds
- smoke tests cover reset, seeded determinism, score bounds, and reward transparency
- Docker can be built and run locally
- the Hugging Face Space serves `/health`, `/tasks`, `/docs`, and `/baseline`
