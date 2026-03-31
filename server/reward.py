from __future__ import annotations


def compute_step_reward(score: float) -> float:
    return max(0.0, min(1.0, score))


def compute_trajectory_reward(
    per_ticket_scores: list[float], queue_size: int, steps_taken: int
) -> float:
    if not per_ticket_scores:
        return 0.0
    avg = sum(per_ticket_scores) / len(per_ticket_scores)
    overshoot = max(0, steps_taken - queue_size)
    penalty = overshoot * 0.03
    return max(0.0, min(1.0, avg - penalty))
