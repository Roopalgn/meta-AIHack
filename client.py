from __future__ import annotations

from typing import Any, Dict, Optional

from openenv.core.env_client import EnvClient, StepResult

from models import HelpdeskTicketAction, HelpdeskTicketObservation, HelpdeskTicketState


class HelpdeskTicketEnvClient(
    EnvClient[HelpdeskTicketAction, HelpdeskTicketObservation, HelpdeskTicketState]
):
    def _step_payload(self, action: HelpdeskTicketAction) -> Dict[str, Any]:
        return action.model_dump(exclude_none=True)

    def _parse_result(
        self, payload: Dict[str, Any]
    ) -> StepResult[HelpdeskTicketObservation]:
        obs_data = payload.get("observation", payload)
        obs = HelpdeskTicketObservation.model_validate(obs_data)
        return StepResult(
            observation=obs,
            reward=payload.get("reward", obs.reward),
            done=payload.get("done", obs.done),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> HelpdeskTicketState:
        return HelpdeskTicketState.model_validate(payload)
