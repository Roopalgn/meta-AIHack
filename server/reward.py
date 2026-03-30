"""
server/reward.py — Reward helpers for the IT Helpdesk Ticket Routing environment.
"""
from __future__ import annotations


def clamp_reward(score: float) -> float:
    """Clamp a score to [0.0, 1.0]."""
    return max(0.0, min(1.0, score))


def trajectory_reward(
    per_ticket_scores: list[float],
    steps_taken: int,
    queue_size: int,
) -> float:
    """
    Compute the final episode reward.

    avg = mean(per_ticket_scores)
    penalty = 0.03 * max(0, steps_taken - queue_size)
    return clamp(avg - penalty)
    """
    if not per_ticket_scores:
        return 0.0
    avg = sum(per_ticket_scores) / len(per_ticket_scores)
    penalty = 0.03 * max(0, steps_taken - queue_size)
    return clamp_reward(avg - penalty)
