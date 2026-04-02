# Hackstreet Boys Final Roadmap

## Team

- Team name: Hackstreet Boys
- Members:
  - Roopal Guha Neogi
  - Suyash Kumar
- Submission deadline: April 8, 2026, 11:59 PM IST

## How To Use This File

- `PROJECT_STATUS.md` is the canonical log of completed work.
- This roadmap is now the remaining execution plan from the current merged repo state to final submission.
- `analysis/comp.md`, `analysis/comp_know.md`, and `analysis/inference.md` are internal prioritization notes only. Use them to guide priorities, but do not mention competitor repos in public-facing docs.

## Current Repo State

The repo has already established the core submission shape:

- locked IT helpdesk ticket routing domain
- locked vocabulary and task names
- 3-task difficulty ladder
- deterministic grading with partial credit
- working heuristic baseline
- merged local validation on `/health`, `/tasks`, and `inference.py`
- current local benchmark reference:
  - Task 1: `1.0000`
  - Task 2: `0.8800`
  - Task 3: `0.9400`
  - Overall: `0.9400`

The remaining work is no longer broad feature development. The remaining work is:

1. final packaging and deployment readiness
2. clean rerun evidence
3. small high-impact improvements that strengthen submission quality without risking regressions
4. freeze and submit early

## Submission Gates That Must Be True

These are the practical must-pass items from `PLAN.md` and `KNOWLEDGE.md`:

- the environment starts correctly
- `reset()`, `step()`, and `state()` behave correctly
- 3 tasks exist and remain meaningfully different
- grader scores stay in `[0.0, 1.0]`
- `inference.py` runs reproducibly without crashing
- Docker builds and starts cleanly
- docs and metadata are current
- the repo is easy for judges to understand and rerun

## Final Priority Order

If time gets tight, prioritize in this exact order:

1. merged Docker and deployment validation
2. clean-copy rerun
3. README and metadata readiness for Hugging Face / OpenEnv deployment
4. small reward and observation improvements that strengthen RL value
5. extra polish

## Ownership From Now Until Submission

### Roopal ownership

Files already owned:

- `data/dataset.json`
- `server/tasks.py`
- `server/grader.py`
- `README.md`
- `KNOWLEDGE.md`
- `MENTAL_MODEL.md`

Roopal mandatory finish-line responsibilities:

- keep the docs judge-friendly and fully current
- add Hugging Face Spaces README frontmatter
- keep the task story and public explanation simple and strong
- make only safe grader improvements that improve reward quality without destabilizing labels
- sync benchmark references in docs if any runtime change alters the numbers

Roopal optional high-value improvements:

- add a short TRL / GRPO usage example to `README.md`
- expand the issue-type similarity matrix with only a few safe, reviewable near-miss pairs
- add one or two sharper hard-case examples in docs if useful

### Suyash ownership

Files already owned:

- `models.py`
- `server/environment.py`
- `server/app.py`
- `server/reward.py`
- `client.py`
- `inference.py`
- `openenv.yaml`
- `server/Dockerfile`
- `pyproject.toml`
- `requirements.txt`

Suyash mandatory finish-line responsibilities:

- keep the runtime stable from the merged branch
- confirm Docker evidence on the merged submission branch
- add `.openenvignore` for cleaner `openenv push` packaging
- verify deployment assumptions around `app_port: 7860`, `/health`, `/docs`, `/ws`, and `/web`
- do a clean-copy install-and-run pass from a fresh clone if possible
- rerun `inference.py` after any runtime-side change

Suyash optional high-value improvements:

- enrich observation history with slightly more useful prior-step context
- support an optional `queue_size` reset kwarg if the change stays tiny and low-risk

### Shared responsibilities

- do not rename schemas or vocabulary
- rerun the benchmark after any code change that could affect behavior
- keep `PROJECT_STATUS.md` honest
- use the GitHub Actions Docker smoke workflow when local Docker is blocked by machine setup
- stop adding risky features before the deadline day

## Improvements Worth Doing Before April 8

These are the best ideas from the competitive analysis that are still worth doing this late.

### P0: Do before submission

- add Hugging Face Spaces frontmatter to `README.md`
- add `.openenvignore`
- make sure the merged branch has a green Docker smoke result
- do one clean-copy rerun outside the current working tree if possible

### P1: Do only if the repo remains stable

- add a short TRL / GRPO integration example to `README.md`
- expand `ISSUE_TYPE_SIMILARITY` with only a few obvious, defensible pairs such as:
  - `onboarding` vs `service_request`
  - `feature_request` vs `service_request`
  - `security_compliance` vs `identity_access`
- enrich `history` slightly if it helps multi-step reasoning and does not bloat observations

### P2: Defer unless everything else is already green

- optional `queue_size` reset override

## Improvements To Avoid Before The Deadline

These ideas came up in the analysis, but they are too risky or too large for the remaining time window:

- MCP migration
- transform-based reward refactor
- large dataset expansion from 45 to 100 tickets
- major schema changes
- broad prompt or inference rewrites that could disturb the stable baseline
- big dependency-management changes just for polish

## Date-By-Date Execution Plan

### April 6, 2026

Primary goal:

- lock down deployment readiness and clean rerun evidence

Roopal:

- add Hugging Face Spaces README frontmatter
- keep judge-facing README language concise and strong
- review whether a small issue-similarity expansion is safe enough to land

Suyash:

- add `.openenvignore`
- verify the Docker smoke workflow on the merged branch
- do a clean-copy install plus `inference.py` rerun from a fresh clone if possible

Shared checkpoint:

- Docker evidence is green
- clean-copy rerun is complete or explicitly blocked
- no stale claims remain in docs

### April 7, 2026

Primary goal:

- only high-signal improvements, then freeze

Roopal:

- add a short TRL / GRPO example if it can be written cleanly
- make at most one final safe grader improvement if benchmark stability is preserved
- do a final docs consistency pass across `README.md`, `KNOWLEDGE.md`, and `MENTAL_MODEL.md`

Suyash:

- make only tiny runtime improvements if they are clearly helpful and low-risk
- otherwise freeze the runtime and packaging files
- rerun the benchmark if any runtime-side change lands

Shared checkpoint:

- final benchmark numbers recorded if unchanged or freshly rerun if changed
- docs, metadata, and runtime all tell the same story
- feature work stops by the end of the day

### April 8, 2026

Primary goal:

- submit from a calm, validated repo state

Morning:

- run one final smoke test on the submission branch
- verify Docker evidence still exists on the merged commit
- verify `README.md`, `openenv.yaml`, and required files are present and current

Afternoon:

- make only typo-level or packaging-only fixes
- do not make risky grader, dataset, or runtime changes

Final submission rule:

- stop risky edits several hours before the 11:59 PM IST deadline
- submit early if the repo is already green

## What Counts As Complete

### April 6 complete means

- merged Docker validation exists
- clean-copy rerun evidence exists or a specific blocker is documented
- deployment-readiness files are in place

### April 7 complete means

- any remaining safe improvements are merged
- final benchmark reference is recorded
- docs and metadata are frozen

### April 8 complete means

- final smoke test is done
- submission has been sent

## Simple Rule To Remember

Roopal owns the story, labels, and public clarity.
Suyash owns the runtime, packaging, and reproducibility rails.
Both of you should optimize for a clean, rerunnable, judge-friendly submission rather than chasing last-minute complexity.
