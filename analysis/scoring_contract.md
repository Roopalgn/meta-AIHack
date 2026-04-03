# Scoring Contract

> Internal note for test design and scorer review

## Goal

Make the helpdesk grader deterministic, defensible, and only fuzzy where we can explain why.

## Exact-Match-Only Fields

These fields should never receive partial credit:

- `assignment_group`
- `resolution_action`

If either is wrong, the field score should be exactly `0.0`.

## Limited Partial-Credit Fields

### `issue_type`

`issue_type` can receive partial credit only for explicitly listed near-miss pairs in `server/grader.py`.

Implications:

- exact match = `1.0`
- listed near miss = configured partial score
- unlisted wrong label = `0.0`

There should be no hidden semantic fuzziness beyond the declared similarity map.

### `priority`

`priority` can receive partial credit only for explicitly listed adjacency / proximity pairs in `server/grader.py`.

Implications:

- exact match = `1.0`
- defined nearby priority = configured partial score
- undefined mismatch = `0.0`

## Task Weight Contract

- Task 1: `issue_type` only
- Task 2: `issue_type` 60%, `priority` 40%
- Task 3:
  - `issue_type` 35%
  - `priority` 20%
  - `assignment_group` 25%
  - `resolution_action` 20%

The weighted score should always stay in `[0.0, 1.0]`.

## What The Tests Must Prove

1. exact matches score `1.0`
2. unsupported task IDs fail clearly
3. only intended issue-type pairs get partial credit
4. unrelated issue types get `0.0`
5. priority proximity follows the declared table exactly
6. assignment group and resolution action remain exact-only
7. task weights apply exactly as documented
8. dataset loading stays robust, including UTF-8 BOM handling

## Review Rule

Before adding any new similarity pair:

1. justify it with a real-world ticket ambiguity
2. make sure it does not blur clearly distinct operational actions
3. add or update a test that proves the intended behavior
