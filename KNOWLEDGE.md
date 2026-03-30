# IT Helpdesk Ticket Routing OpenEnv - Knowledge Guide

## Part 1: What The Hackathon Wants

The hackathon is asking for a real-world environment that an AI agent can learn from through the standard OpenEnv interface.

In plain terms, the judges want:

1. a real human job, not a toy problem
2. typed models for actions, observations, and state
3. `reset()`, `step()`, and `state()`
4. at least 3 tasks with increasing difficulty
5. deterministic graders that return scores from `0.0` to `1.0`
6. a meaningful reward function
7. a baseline `inference.py`
8. Docker and deployment readiness

## Part 2: Why This Repo Uses IT Helpdesk Ticket Routing

IT helpdesk ticket routing is a strong OpenEnv domain because it is:

- a real operational workflow
- naturally multi-step
- easy to express with typed actions and observations
- easy to score deterministically
- useful for evaluating planning, classification, and routing ability in agents

## Part 3: The Core Mental Model

Think of this environment as a queue of helpdesk tickets.

For each ticket, the agent must answer:

- what kind of issue is this
- how urgent is it
- which resolver group should own it
- what should happen next

The environment shows one ticket at a time. The agent responds with structured fields. The grader scores that response. Then the environment moves to the next ticket.

## Part 4: Main Files

### `models.py`

Defines the typed objects used everywhere:

- `HelpdeskTicketRecord`
- `HelpdeskTicketAction`
- `HelpdeskTicketObservation`
- `HelpdeskTicketState`

### `server/environment.py`

This is the core engine.

It:

- loads the dataset
- samples a queue of 3 to 5 tickets
- tracks progress
- grades each step
- computes the final episode reward

### `server/grader.py`

Contains deterministic scoring logic.

It gives:

- exact or partial credit for `issue_type`
- exact or proximity credit for `priority`
- exact credit for `assignment_group`
- exact credit for `resolution_action`

### `server/reward.py`

Contains reward helpers:

- per-step reward clamping
- final trajectory reward calculation

### `server/tasks.py`

Defines the difficulty ladder:

- Task 1: issue type only
- Task 2: issue type plus priority
- Task 3: full routing

### `server/app.py`

Creates the OpenEnv app and exposes a custom `/tasks` route.

### `client.py`

Typed client used by the inference script.

### `inference.py`

The baseline agent runner.

It can:

- use a real LLM through an OpenAI-compatible API
- or fall back to a keyword heuristic

## Part 5: Tasks

### Task 1: Issue Type Classification

The agent predicts:

- `issue_type`

### Task 2: Issue Type And Priority

The agent predicts:

- `issue_type`
- `priority`

### Task 3: Full Ticket Routing

The agent predicts:

- `issue_type`
- `priority`
- `assignment_group`
- `resolution_action`

## Part 6: Ticket Vocabulary

### Issue types

- `billing_license`
- `identity_access`
- `application_support`
- `service_request`
- `spam_phishing`
- `general_inquiry`
- `security_compliance`
- `onboarding`
- `feature_request`

### Priorities

- `critical`
- `high`
- `medium`
- `low`

### Assignment groups

- `license_ops`
- `service_desk`
- `application_team`
- `procurement`
- `security_team`
- `onboarding_ops`

### Resolution actions

- `fulfill`
- `escalate`
- `assign`
- `ignore`
- `acknowledge`

## Part 7: Episode Flow

### `reset()`

Starts a new episode:

1. chooses a task
2. samples a queue of tickets
3. resets state
4. returns the first observation

### `step(action)`

Processes one ticket:

1. grades the action
2. stores the score
3. advances the queue index
4. returns the next ticket or the final reward

### `state`

Returns the internal state snapshot.

## Part 8: Reward Logic

Step reward:

- just the current ticket score clamped to `[0.0, 1.0]`

Final reward:

- average of all per-ticket scores
- minus a small overshoot penalty if too many steps were taken

This keeps the signal dense and easy to interpret.

## Part 9: Dataset Shape

Each ticket record contains:

- `ticket_id`
- `title`
- `requester`
- `description`
- `issue_type`
- `priority`
- `assignment_group`
- `resolution_action`
- optional `ambiguity_note`
- optional `related_ticket_id`

The current dataset contains 45 tickets.

It includes:

- straightforward tickets
- ambiguous tickets
- follow-up references to earlier tickets

## Part 10: Inference Script In Simple Terms

`inference.py` is the script that actually "plays" the environment.

For each task it:

1. connects to the server
2. resets the environment
3. reads the current ticket
4. decides an action
5. sends the action back
6. collects scores
7. prints a summary

If LLM credentials are available, it uses an LLM.
If not, it uses keyword rules.

## Part 11: What Still Needs Verification

The important next checks are:

1. run the server locally
2. verify the ticket-routing client path works end to end
3. rerun `inference.py`
4. record fresh baseline scores
5. validate Docker and OpenEnv behavior

## Part 12: One-Minute Summary

If you only remember one thing, remember this:

- this repo is now an IT helpdesk ticket router
- the mechanics are still the same multi-step OpenEnv pattern
- one ticket is shown at a time
- the agent predicts structured routing fields
- the grader gives deterministic partial credit
- `inference.py` is the baseline agent runner
