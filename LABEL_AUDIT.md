# Label Audit Notes

This file records the March 31 and April 1 label-and-grader pass on the Roopal-owned files:

- `data/dataset.json`
- `server/tasks.py`
- `server/grader.py`

## Dataset Decisions

### Tightened ambiguity cases

- `ticket-022`
  Reworded to make the billing-versus-application ambiguity clearer while keeping the chosen label as `application_support`.

- `ticket-027`
  Reworded to make the vendor-offer ambiguity clearer between `general_inquiry` and `service_request`.

- `ticket-029`
  Reworded to make the seat-expansion versus prorating ambiguity clearer and changed `resolution_action` from `fulfill` to `assign`.

- `ticket-040`
  Reworded to make the feature-gap versus support-issue ambiguity clearer.

### Corrected label consistency

- `ticket-026`
  Changed from `feature_request` / `application_team` to `general_inquiry` / `service_desk` because it is a thank-you note, not a product change request.

## Task Wording Changes

The task instructions in `server/tasks.py` were tightened so they now:

- sound more like helpdesk triage
- emphasize choosing the single best label
- describe operational priority more clearly
- describe full triage more concretely for Task 3

## Grader Changes

The grader was polished by:

- making task weights explicit in `TASK_WEIGHTS`
- adding partial-credit pairs for:
  - `application_support` vs `feature_request`
  - `general_inquiry` vs `service_request`
- keeping the scoring deterministic and task-specific

## Intent

These edits are meant to improve:

- dataset realism
- label consistency
- hard-task ambiguity quality
- reviewability for judges and teammates
