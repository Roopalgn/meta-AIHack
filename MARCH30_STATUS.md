# March 30 Status Report

This file captures the code checkpoint completed for March 30, 2026 so both Codex sessions can compare against the same source of truth.

## Scope Completed

The March 30 code checkpoint is complete for the foundational files named in `ROADMAP.md`:

- `models.py`
- `server/tasks.py`
- `server/grader.py`
- `server/environment.py`

Related supporting files were also aligned:

- `client.py`
- `server/app.py`
- `inference.py`
- `vocabulary.py`

## What Is Locked

### Team and project identity

- Team: Hackstreet Boys
- Members: Roopal Guha Neogi, Suyash Kumar
- Domain: IT Helpdesk Ticket Routing

### Frozen class names

- `HelpdeskTicketRecord`
- `HelpdeskTicketAction`
- `HelpdeskTicketObservation`
- `HelpdeskTicketState`
- `HelpdeskTicketRoutingEnvironment`
- `HelpdeskTicketEnvClient`

### Frozen field names

- `ticket_id`
- `title`
- `requester`
- `description`
- `issue_type`
- `priority`
- `assignment_group`
- `resolution_action`
- `related_ticket_id`

## Code That Exists Now

### `vocabulary.py`

Shared frozen constants now live in one place:

- team metadata
- environment names
- issue types
- priorities
- assignment groups
- resolution actions
- default issue-type mappings used by inference

### `models.py`

The typed models are defined and the vocabulary is enforced through validators, so unsupported labels should fail fast instead of silently drifting.

### `server/tasks.py`

All three tasks are defined with locked names, instructions, and allowed fields.

### `server/grader.py`

Deterministic scoring is in place with:

- partial credit for near-miss `issue_type`
- proximity scoring for `priority`
- exact match for `assignment_group`
- exact match for `resolution_action`

### `server/environment.py`

The environment implements:

- queue sampling
- reset flow
- step flow
- state tracking
- final trajectory reward handoff

### `inference.py`

The baseline runner is aligned to the locked vocabulary and supports:

- LLM mode
- heuristic mode
- task loop over all 3 tasks

## Expected Agreement For The Other Codex Session

Your teammate's Codex should agree on all of the following:

1. the schema names above are frozen
2. the vocabulary now has a single source of truth in `vocabulary.py`
3. no one should rename labels after this checkpoint
4. future work should build on these names, not replace them

## What Is Not Verified Yet

This checkpoint is a code-and-consistency checkpoint, not a runtime-complete checkpoint.

Still pending:

- local execution
- heuristic baseline run
- Docker validation
- final benchmark numbers
