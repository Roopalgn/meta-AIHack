"""
server/environment.py — Core OpenEnv environment for IT Helpdesk Ticket Routing.

Implements reset(), step(), and state() against the ticket queue model.
"""
from __future__ import annotations

import random
import uuid
from typing import Any, Optional

from openenv.core.env_server.base_env import BaseEnvironment

from models import (
    HelpdeskTicketAction,
    HelpdeskTicketObservation,
    HelpdeskTicketRecord,
    HelpdeskTicketState,
)
from server.grader import grade
from server.reward import clamp_reward, trajectory_reward
from server.tasks import TaskDefinition, get_task, load_dataset

# Queue size bounds
_QUEUE_MIN = 3
_QUEUE_MAX = 5


class HelpdeskTicketRoutingEnvironment(BaseEnvironment):
    """
    Multi-step IT helpdesk ticket routing environment.

    One ticket is shown per step. The agent predicts routing fields.
    The grader scores each prediction. The final reward is the trajectory average.
    """

    def __init__(self) -> None:
        self._dataset: list[dict] = load_dataset()
        self._task: Optional[TaskDefinition] = None
        self._seed: Optional[int] = None
        self._queue: list[HelpdeskTicketRecord] = []
        self._index: int = 0
        self._scores: list[float] = []
        self._episode_id: str = ""

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(
        self,
        seed: Optional[int] = None,
        task_id: Optional[int] = None,
        **kwargs: Any,
    ) -> HelpdeskTicketObservation:
        task_id = task_id or 1
        self._task = get_task(task_id)
        self._seed = seed if seed is not None else random.randint(0, 2**31)
        self._episode_id = str(uuid.uuid4())

        rng = random.Random(self._seed)
        queue_size = rng.randint(_QUEUE_MIN, _QUEUE_MAX)
        sampled = rng.sample(self._dataset, min(queue_size, len(self._dataset)))
        self._queue = [HelpdeskTicketRecord(**t) for t in sampled]

        self._index = 0
        self._scores = []

        return self._build_observation(done=False, reward=0.0)

    def step(
        self,
        action: HelpdeskTicketAction,
        **kwargs: Any,
    ) -> HelpdeskTicketObservation:
        if self._task is None or not self._queue:
            raise RuntimeError("Call reset() before step()")

        current = self._queue[self._index]
        action_dict = action.model_dump(exclude_none=True)
        score = grade(action_dict, current.model_dump(), self._task.id)
        self._scores.append(score)
        self._index += 1

        if self._index < len(self._queue):
            return self._build_observation(done=False, reward=clamp_reward(score))

        # Episode complete
        final = trajectory_reward(self._scores, self._index, len(self._queue))
        return self._build_observation(done=True, reward=final)

    def state(self) -> HelpdeskTicketState:
        return HelpdeskTicketState(
            current_task_id=self._task.id if self._task else None,
            seed=self._seed,
            queue_ticket_ids=[t.ticket_id for t in self._queue],
            current_ticket_index=self._index,
            per_ticket_scores=list(self._scores),
            total_reward=(
                sum(self._scores) / len(self._scores) if self._scores else 0.0
            ),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_observation(self, done: bool, reward: float) -> HelpdeskTicketObservation:
        assert self._task is not None

        if not done and self._index < len(self._queue):
            current_ticket = self._public_ticket(self._queue[self._index])
        else:
            current_ticket = None

        tickets_processed = self._index
        tickets_remaining = max(0, len(self._queue) - self._index)

        history = [
            {
                "step": i + 1,
                "ticket_id": self._queue[i].ticket_id,
                "score": self._scores[i],
            }
            for i in range(len(self._scores))
        ]

        return HelpdeskTicketObservation(
            task_id=self._task.id,
            task_name=self._task.name,
            instructions=self._task.instructions,
            allowed_fields=list(self._task.allowed_fields),
            current_ticket=current_ticket,
            queue_size=len(self._queue),
            tickets_remaining=tickets_remaining,
            tickets_processed=tickets_processed,
            history=history,
            reward=reward,
            done=done,
        )

    @staticmethod
    def _public_ticket(record: HelpdeskTicketRecord) -> dict[str, str]:
        """Return only the fields the agent is allowed to see."""
        return {
            "ticket_id": record.ticket_id,
            "title": record.title,
            "requester": record.requester,
            "description": record.description,
        }
