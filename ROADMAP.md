# Hackstreet Boys Roadmap

## Team

- Team name: Hackstreet Boys
- Members:
  - Roopal Guha Neogi
  - Suyash Kumar
- Submission deadline: April 8, 2026, 11:59 PM IST

## Goal

Ship a clean, well-documented OpenEnv environment for IT helpdesk ticket routing that:

- passes all submission gates
- scores well on real-world utility
- has deterministic, defensible grading
- is easy for judges to understand and rerun

## When You Start Coding

Start coding immediately on **March 30, 2026** after a short 30 to 60 minute alignment pass.

That first coding session should do only high-leverage foundation work:

- lock the exact ticket vocabulary
- freeze field names in `models.py`
- confirm task fields in `server/tasks.py`
- agree on grader labels in `server/grader.py`
- agree that no one changes schema names casually after this point

### First coding targets on March 30, 2026

Roopal should start with:

- `data/dataset.json`
- `server/tasks.py`
- `server/grader.py`

Suyash should start with:

- `models.py`
- `server/environment.py`
- `inference.py`

By the end of the first coding block, both of you should have:

- matching field names
- matching task labels
- matching issue-type vocabulary
- no unresolved schema disagreements

## Working Model For Two People

The safest way for two people to work separately and merge cleanly is to divide ownership by file groups, not by abstract ideas.

### Roopal ownership

- `data/dataset.json`
- `server/tasks.py`
- `server/grader.py`
- `README.md`
- `KNOWLEDGE.md`
- `MENTAL_MODEL.md`

Primary responsibilities:

- dataset quality
- label consistency
- task wording
- grader realism
- documentation clarity
- judging-story polish

### Suyash ownership

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

Primary responsibilities:

- runtime correctness
- OpenEnv interface
- inference reliability
- Docker and deployment readiness
- integration behavior

## Merge Strategy

To keep parallel work easy to combine:

1. avoid editing the same file on the same day unless planned
2. use one shared terminology list and do not invent alternate labels
3. sync once daily with a 10 minute review of:
   - changed files
   - open blockers
   - any schema changes
4. freeze the dataset schema early
5. freeze the action and observation field names early

## Shared Source Of Truth

These files should be treated as authoritative:

- `README.md` for the public project story
- `PLAN.md` for project requirements and definition of done
- `MENTAL_MODEL.md` for the current system shape
- `openenv.yaml` for environment metadata
- `server/tasks.py` and `server/grader.py` for task rules

## AI Usage Policy

AI is permitted, so use it aggressively where it saves time, but do not outsource judgment.

Good uses of AI:

- draft clearer task descriptions
- propose additional hard-case tickets
- suggest edge cases and label audits
- improve prompts in `inference.py`
- generate test ideas and checklists
- improve README structure and wording

Human review required for:

- final dataset labels
- grader weights and partial-credit rules
- any claims in README
- final benchmark numbers
- submission metadata and deployment settings

## Submission Criteria Checklist

### Must pass

- environment starts correctly
- `reset()`, `step()`, and `state()` behave correctly
- 3 tasks exist and are meaningfully different
- grader scores are in `[0.0, 1.0]`
- `inference.py` runs without error
- Docker builds and starts
- docs are complete and current

### Must score well

- the task feels like real IT helpdesk work
- the hard task is genuinely harder
- the grader gives partial credit in sensible ways
- the environment is easy to understand and rerun

## Timeline

### March 30, 2026

- lock team name, domain, and vocabulary
- finish repo cleanup
- agree on ownership split
- start coding the core schema and task logic immediately after the vocabulary lock
- target a same-day checkpoint on:
  - `models.py`
  - `server/tasks.py`
  - `server/grader.py`
  - `server/environment.py`

### March 31, 2026

Roopal:

- audit `data/dataset.json` labels end to end
- tighten ambiguous cases
- review task wording in `server/tasks.py`
- continue code work in `server/grader.py` if partial-credit tuning is still needed

Suyash:

- sanity-check `models.py`, `server/environment.py`, and `client.py`
- check that the field names align everywhere
- continue code work in `inference.py` and `server/app.py`

Shared checkpoint:

- confirm no schema changes are still pending

### April 1, 2026

Roopal:

- polish `server/grader.py`
- confirm hard-task logic and partial-credit behavior
- finish any remaining dataset label corrections

Suyash:

- polish `inference.py`
- confirm heuristic mode uses the new ticket vocabulary consistently
- finish runtime code adjustments in `client.py`, `server/app.py`, and `server/reward.py`

Shared checkpoint:

- agree on the exact labels and examples used in docs

### April 2, 2026

Roopal:

- improve `README.md`
- improve `KNOWLEDGE.md`

Suyash:

- validate `openenv.yaml`
- validate `server/Dockerfile`
- validate dependency files

Shared checkpoint:

- ensure docs and code tell the same story

### April 3, 2026

Roopal:

- do a dataset realism pass
- make sure examples clearly cover easy, medium, and hard cases

Suyash:

- perform the first full local runtime pass
- run heuristic inference
- note bugs or schema mismatches

Shared checkpoint:

- bug triage and fix list

### Practical coding rule

If you are wondering "should we still be planning or should we code now?", the answer is:

- **March 30 to April 4, 2026 = active coding and fixes**
- **April 5 to April 6, 2026 = validation, docs, and score recording**
- **April 7 to April 8, 2026 = freeze, smoke tests, and submission**

### April 4, 2026

Roopal:

- fix data, wording, and documentation issues from runtime feedback

Suyash:

- fix environment, inference, and Docker issues from runtime feedback

Shared checkpoint:

- second full local run

### April 5, 2026

Roopal:

- finalize README and knowledge docs
- prepare a concise judge-facing explanation of the domain

Suyash:

- confirm Docker flow
- confirm all required env vars are documented and handled

Shared checkpoint:

- record benchmark numbers if stable

### April 6, 2026

- full dry run from a clean copy if possible
- verify every required file is present
- check for stale claims and outdated wording

### April 7, 2026

- freeze feature changes
- only bug fixes, validation, and submission packaging
- verify final docs, metadata, and benchmark numbers

### April 8, 2026

- do one last deployment and smoke test early in the day
- stop risky edits several hours before deadline
- submit before 11:59 PM IST

## Integration Rules

To keep merges painless:

1. do not rename schemas after April 1, 2026
2. do not change task labels after April 2, 2026 without both agreeing
3. do not edit ownership files casually
4. if one person must touch the other person's file, call it out before doing it
5. keep a short daily changelog in chat or a shared note

## Definition Of Done For Each Member

### Roopal done means

- dataset labels are internally consistent
- docs are submission-ready
- the hard task feels meaningfully harder than the easy and medium tasks

### Suyash done means

- the environment runs end to end
- the inference script works in heuristic mode
- Docker and metadata are in good shape

## Final Two-Day Priority Order

If time gets tight, prioritize in this exact order:

1. working environment
2. working inference script
3. valid grader and tasks
4. Docker and metadata
5. README clarity
6. extra polish

## Simple Rule To Remember

Roopal owns the story and the labels.
Suyash owns the runtime and the rails.
Both review the final submission together.
