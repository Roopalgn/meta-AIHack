# IT Helpdesk Ticket Routing OpenEnv

> Meta PyTorch OpenEnv Hackathon - Round 1 Submission
> Team Hackstreet Boys - Roopal Guha Neogi, Suyash Kumar

A deterministic, multi-step IT helpdesk ticket routing environment built on the OpenEnv framework. An AI agent receives a small queue of helpdesk tickets and must classify the issue type, estimate priority, assign the correct resolver group, and choose the best next action.

## Why IT Helpdesk Ticket Routing?

IT service desks do this work every day:

- read a newly created ticket
- decide what kind of issue it is
- judge urgency
- route it to the right team
- decide whether to fulfill, escalate, assign, ignore, or acknowledge it

This makes the domain:

- genuinely real-world
- easy to evaluate deterministically
- naturally multi-step
- well aligned with enterprise support and agent-routing workflows

## Architecture

```text
inference.py
    |
    v
client.py  <---->  server/app.py
                         |
                         v
                server/environment.py
                  |       |        |
                  v       v        v
            grader.py  reward.py  tasks.py
                                  |
                                  v
                           data/dataset.json
```

Key architectural detail:

- the environment is designed as a multi-step ticket queue
- the client path is used for persistent episode flow
- the environment still follows the standard OpenEnv `reset()`, `step()`, and `state()` interface

## Tasks

| ID | Name | Difficulty | Fields Required | Description |
|----|------|------------|-----------------|-------------|
| 1 | Issue Type Classification | Easy | `issue_type` | Classify the ticket into the correct IT issue type |
| 2 | Issue Type And Priority | Medium | `issue_type`, `priority` | Classify the issue and estimate urgency |
| 3 | Full Ticket Routing | Hard | `issue_type`, `priority`, `assignment_group`, `resolution_action` | Perform full helpdesk routing |

## Action Space

The agent submits a `HelpdeskTicketAction`. Only the fields relevant to the current task are scored.

```json
{
  "issue_type": "billing_license | identity_access | application_support | service_request | spam_phishing | general_inquiry | security_compliance | onboarding | feature_request",
  "priority": "critical | high | medium | low",
  "assignment_group": "license_ops | service_desk | application_team | procurement | security_team | onboarding_ops",
  "resolution_action": "fulfill | escalate | assign | ignore | acknowledge"
}
```

## Observation Space

Each observation contains:

- `task_id`
- `task_name`
- `instructions`
- `allowed_fields`
- `current_ticket`
- `queue_size`
- `tickets_remaining`
- `tickets_processed`
- `history`
- inherited OpenEnv fields such as `done` and `reward`

The visible ticket fields are:

- `ticket_id`
- `title`
- `requester`
- `description`

Ground-truth labels are not exposed to the agent.

## State

The internal `HelpdeskTicketState` tracks:

- `episode_id`
- `step_count`
- `current_task_id`
- `seed`
- `queue_ticket_ids`
- `current_ticket_index`
- `per_ticket_scores`
- `total_reward`

## Grading

Scoring is deterministic and ranges from `0.0` to `1.0`.

### Per-field logic

- `issue_type`: exact match or partial credit for near-miss pairs
- `priority`: exact match or proximity score
- `assignment_group`: exact match
- `resolution_action`: exact match

### Task weights

| Task | Issue Type | Priority | Assignment Group | Resolution Action |
|------|------------|----------|------------------|-------------------|
| 1 | 100% | - | - | - |
| 2 | 60% | 40% | - | - |
| 3 | 35% | 20% | 25% | 20% |

### Trajectory reward

At episode end:

```text
trajectory_reward = average(per_ticket_scores) - 0.03 * max(0, steps_taken - queue_size)
```

The result is clamped to `[0.0, 1.0]`.

## Dataset

`data/dataset.json` contains 45 labeled helpdesk tickets covering:

- issue classification
- access requests
- application incidents
- procurement and service requests
- phishing or spam reports
- security and compliance work
- onboarding tickets
- feature requests

The dataset also includes:

- ambiguous cases
- follow-up thread references
- multiple priority levels

## Project Structure

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
openenv.yaml
pyproject.toml
requirements.txt
README.md
KNOWLEDGE.md
PLAN.md
MENTAL_MODEL.md
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Basic checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/tasks
```

## Running Inference

### LLM mode

Set:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Then run:

```bash
python inference.py
```

### Heuristic mode

If those variables are not set, the script falls back to a keyword-based ticket router:

```bash
python inference.py
```

Optional server target:

- `ENV_URL` default: `http://localhost:8000`

## Docker

Build and run:

```bash
docker build -f server/Dockerfile -t helpdesk-ticket-routing .
docker run -p 7860:7860 helpdesk-ticket-routing
```

## API Endpoints

OpenEnv auto-generates the main endpoints, and the repo adds `/tasks`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/reset` | Start a new episode |
| POST | `/step` | Submit an action |
| GET | `/state` | Inspect state |
| WebSocket | `/ws` | Persistent client channel |
| GET | `/tasks` | List available tasks |
| GET | `/docs` | API docs |

## Baseline Status

Fresh baseline scores should be recorded after the next validation pass. The recommended order is:

1. run the environment locally
2. run the heuristic baseline in `inference.py`
3. record per-task and overall scores
4. update the docs only after those numbers are verified
