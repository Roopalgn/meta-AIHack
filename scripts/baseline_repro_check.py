#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import inference
from models import HelpdeskTicketAction
from server.environment import HelpdeskTicketRoutingEnvironment


def _parse_int_spec(spec: str) -> list[int]:
    values: list[int] = []
    for chunk in spec.split(","):
        token = chunk.strip()
        if not token:
            continue
        if "-" in token:
            start_raw, end_raw = token.split("-", 1)
            start = int(start_raw)
            end = int(end_raw)
            if end < start:
                raise ValueError(f"Range must be ascending: {token!r}")
            values.extend(range(start, end + 1))
        else:
            values.append(int(token))
    if not values:
        raise ValueError("Expected at least one integer value")
    deduped: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _run_baseline_episode(task_id: int, seed: int) -> dict[str, Any]:
    env = HelpdeskTicketRoutingEnvironment()
    obs = env.reset(seed=seed, task_id=task_id)
    step_count = 0

    while not obs.done:
        ticket = obs.current_ticket
        if ticket is None:
            break

        while getattr(obs, "investigation_budget_remaining", 0) > 0:
            investigate, tool_name = inference.should_investigate(
                ticket,
                obs.history,
                list(getattr(obs, "available_tools", []) or []),
            )
            if not investigate or tool_name is None:
                break
            investigate_action = HelpdeskTicketAction(
                action_type="investigate",
                tool_name=tool_name,
                tool_target_ticket_id=ticket.get("related_ticket_id"),
            )
            obs = env.step(investigate_action)
            step_count += 1
            if obs.done:
                break
            ticket = obs.current_ticket
            if ticket is None:
                break

        if obs.done:
            break
        ticket = obs.current_ticket
        if ticket is None:
            break

        ticket_with_context = inference.merge_ticket_context(ticket, obs)
        operational_action, _ = inference.choose_operational_action(
            ticket_with_context,
            obs.history,
            list(getattr(obs, "available_action_types", []) or []),
        )
        if operational_action is not None:
            obs = env.step(operational_action)
            step_count += 1
            continue

        submit_action, _, _ = inference.build_action(
            ticket_with_context,
            obs.allowed_fields,
            obs.instructions,
        )
        obs = env.step(submit_action)
        step_count += 1

    final_score = float(obs.rubric_reward if obs.rubric_reward is not None else (obs.reward or 0.0))
    return {
        "task_id": task_id,
        "seed": seed,
        "score": round(final_score, 6),
        "steps": step_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic baseline rollouts on fixed seeds and enforce an "
            "expected score range for regression checks."
        )
    )
    parser.add_argument(
        "--seeds",
        default="42-46",
        help="Comma-separated seeds or ranges (for example: 42-46 or 42,50,60).",
    )
    parser.add_argument(
        "--task-ids",
        default="1,2,3",
        help="Comma-separated task IDs or ranges.",
    )
    parser.add_argument(
        "--expect-min",
        type=float,
        default=0.40,
        help="Minimum acceptable overall average score across all seed-task episodes.",
    )
    parser.add_argument(
        "--expect-max",
        type=float,
        default=0.95,
        help="Maximum acceptable overall average score across all seed-task episodes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full JSON details in addition to the human-readable summary.",
    )
    args = parser.parse_args()

    seeds = _parse_int_spec(args.seeds)
    task_ids = _parse_int_spec(args.task_ids)
    rollouts: list[dict[str, Any]] = []

    for seed in seeds:
        for task_id in task_ids:
            rollouts.append(_run_baseline_episode(task_id=task_id, seed=seed))

    per_seed_average: dict[int, float] = {}
    for seed in seeds:
        seed_scores = [item["score"] for item in rollouts if item["seed"] == seed]
        per_seed_average[seed] = round(mean(seed_scores), 6)

    all_scores = [item["score"] for item in rollouts]
    overall_average = round(mean(all_scores), 6)
    observed_min = round(min(all_scores), 6)
    observed_max = round(max(all_scores), 6)

    print(
        (
            "[BASELINE] "
            f"seeds={seeds} task_ids={task_ids} episodes={len(rollouts)} "
            f"overall_avg={overall_average:.4f} score_min={observed_min:.4f} score_max={observed_max:.4f}"
        ),
        flush=True,
    )
    print(
        (
            "[BASELINE] "
            f"expected_overall_avg_range=[{args.expect_min:.4f}, {args.expect_max:.4f}] "
            f"per_seed_avg={per_seed_average}"
        ),
        flush=True,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "seeds": seeds,
                    "task_ids": task_ids,
                    "expect_min": args.expect_min,
                    "expect_max": args.expect_max,
                    "overall_average": overall_average,
                    "observed_min": observed_min,
                    "observed_max": observed_max,
                    "per_seed_average": per_seed_average,
                    "episodes": rollouts,
                },
                indent=2,
                sort_keys=True,
            ),
            flush=True,
        )

    if not (args.expect_min <= overall_average <= args.expect_max):
        raise SystemExit(
            (
                "Baseline average score regression: "
                f"{overall_average:.4f} is outside [{args.expect_min:.4f}, {args.expect_max:.4f}]"
            )
        )


if __name__ == "__main__":
    main()
