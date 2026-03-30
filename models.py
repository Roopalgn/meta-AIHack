from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field
from openenv.core.env_server.types import Action, Observation, State


class HelpdeskTicketRecord(BaseModel):
    ticket_id: str
    title: str
    requester: str
    description: str
    issue_type: str
    priority: str
    assignment_group: str
    resolution_action: str
    ambiguity_note: Optional[str] = None
    related_ticket_id: Optional[str] = None


class HelpdeskTicketAction(Action):
    issue_type: Optional[str] = None
    priority: Optional[str] = None
    assignment_group: Optional[str] = None
    resolution_action: Optional[str] = None


class HelpdeskTicketObservation(Observation):
    task_id: int = 0
    task_name: str = ""
    instructions: str = ""
    allowed_fields: list[str] = Field(default_factory=list)
    current_ticket: Optional[dict[str, str]] = None
    queue_size: int = 0
    tickets_remaining: int = 0
    tickets_processed: int = 0
    history: list[dict[str, Any]] = Field(default_factory=list)


class HelpdeskTicketState(State):
    episode_id: str = ""
    step_count: int = 0
    current_task_id: Optional[int] = None
    seed: Optional[int] = None
    queue_ticket_ids: list[str] = Field(default_factory=list)
    current_ticket_index: int = 0
    per_ticket_scores: list[float] = Field(default_factory=list)
    total_reward: float = 0.0
