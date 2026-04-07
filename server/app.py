import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path so `models` and `server` are importable
_repo_root = str(Path(__file__).resolve().parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from fastapi import HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse
from openenv.core.env_server import create_app

from models import HelpdeskTicketAction, HelpdeskTicketObservation
from server.environment import HelpdeskTicketRoutingEnvironment
from server.grader import grade_action
from server.tasks import TASKS, load_dataset
from vocabulary import APP_ENV_NAME

app = create_app(
    HelpdeskTicketRoutingEnvironment,
    HelpdeskTicketAction,
    HelpdeskTicketObservation,
    env_name=APP_ENV_NAME,
)


class GraderRequest(BaseModel):
    task_id: int
    ticket_id: str
    action: dict[str, Any]


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/web", status_code=307)


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {
                "id": t["id"],
                "name": t["name"],
                "difficulty": t["difficulty"],
                "instructions": t["instructions"],
                "allowed_fields": t["allowed_fields"],
            }
            for t in TASKS.values()
        ]
    }


@app.get("/web", response_class=HTMLResponse)
def web_ui():
    task_rows = "".join(
        f"<tr><td>{t['id']}</td><td>{t['name']}</td><td>{t['difficulty']}</td></tr>"
        for t in TASKS.values()
    )
    html = f"""<!DOCTYPE html>
<html><head><title>{APP_ENV_NAME}</title></head>
<body>
<h1>{APP_ENV_NAME}</h1>
<p>Version: 0.1.0 | <a href="/health">Health</a> | <a href="/docs">API Docs</a></p>
<h2>Tasks</h2>
<table border="1"><tr><th>ID</th><th>Name</th><th>Difficulty</th></tr>
{task_rows}
</table>
</body></html>"""
    return HTMLResponse(content=html)


def _build_baseline_submit_action(
    ticket: dict[str, Any], allowed_fields: list[str]
) -> HelpdeskTicketAction:
    import inference

    candidate = inference.heuristic_action(ticket, allowed_fields)
    candidate, _ = inference.apply_domain_overrides(ticket, candidate, allowed_fields)
    return HelpdeskTicketAction(**candidate)


@app.get("/baseline")
def baseline_rollout(task_id: int = 1, seed: int = 42):
    import inference

    env = HelpdeskTicketRoutingEnvironment()
    observation = env.reset(seed=seed, task_id=task_id)
    steps: list[dict[str, Any]] = []

    while not observation.done:
        ticket = observation.current_ticket
        if ticket is None:
            break

        investigate, tool_name = inference.should_investigate(ticket, observation.history)
        if (
            investigate
            and tool_name is not None
            and observation.investigation_budget_remaining > 0
        ):
            investigate_action = HelpdeskTicketAction(
                action_type="investigate",
                tool_name=tool_name,
                tool_target_ticket_id=ticket.get("related_ticket_id"),
            )
            observation = env.step(investigate_action)
            steps.append(
                {
                    "action": investigate_action.model_dump(exclude_none=True),
                    "reward": observation.reward,
                    "done": observation.done,
                    "action_source": "baseline_investigate",
                }
            )
            if observation.done:
                break
            ticket = observation.current_ticket
            if ticket is None:
                break

        action = _build_baseline_submit_action(
            inference.merge_ticket_context(ticket, observation),
            list(observation.allowed_fields),
        )
        observation = env.step(action)
        steps.append(
            {
                "action": action.model_dump(exclude_none=True),
                "reward": observation.reward,
                "done": observation.done,
                "action_source": "baseline_submit",
            }
        )

    return {
        "task_id": task_id,
        "seed": seed,
        "step_count": len(steps),
        "final_reward": observation.reward,
        "rubric_reward": observation.rubric_reward,
        "steps": steps,
    }


@app.post("/grader")
def grader_preview(request: GraderRequest):
    ticket = next(
        (record for record in load_dataset() if record.ticket_id == request.ticket_id),
        None,
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticket_id: {request.ticket_id}")

    try:
        action = HelpdeskTicketAction.model_validate(request.action)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    score, breakdown = grade_action(action, ticket, request.task_id)
    return {
        "task_id": request.task_id,
        "ticket_id": request.ticket_id,
        "score": score,
        "breakdown": breakdown,
        "expected": {
            "issue_type": ticket.issue_type,
            "priority": ticket.priority,
            "assignment_group": ticket.assignment_group,
            "resolution_action": ticket.resolution_action,
        },
        "submitted": action.model_dump(exclude_none=True),
    }


def main() -> None:
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()
