from __future__ import annotations

import os
import sys
import types as _types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import openenv_test_stubs  # noqa: F401

if "openenv.core.env_server.interfaces" not in sys.modules:
    _interfaces_mod = _types.ModuleType("openenv.core.env_server.interfaces")

    class _Environment:
        def __init__(self) -> None:
            pass

        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__(**kwargs)

        @classmethod
        def __class_getitem__(cls, item: object) -> type:
            return cls

    _interfaces_mod.Environment = _Environment  # type: ignore[attr-defined]
    sys.modules["openenv.core.env_server.interfaces"] = _interfaces_mod

from models import HelpdeskTicketAction
from server.environment import HelpdeskTicketRoutingEnvironment
from server.reward import clamp_open_unit_interval
from server.tasks import load_dataset


class RewardTransparencyTests(unittest.TestCase):
    def _single_ticket_env(self, ticket_id: str) -> tuple[HelpdeskTicketRoutingEnvironment, object]:
        dataset = load_dataset()
        ticket = next((record for record in dataset if record.ticket_id == ticket_id), None)
        self.assertIsNotNone(ticket, f"Missing ticket {ticket_id}")

        env = HelpdeskTicketRoutingEnvironment()
        with patch.object(env, "_dataset", [ticket]):
            with patch.object(env, "_tickets_by_id", {ticket.ticket_id: ticket}):
                obs = env.reset(seed=0, task_id=3, queue_size=1)
        return env, obs

    def test_terminal_reward_components_balance_penalties(self) -> None:
        env, obs = self._single_ticket_env("TKT-NONDEFAULT-003")
        ticket = env._queue[0]  # noqa: SLF001 - deterministic test fixture

        final_obs = env.step(
            HelpdeskTicketAction(
                issue_type=ticket.issue_type,
                priority=ticket.priority,
                assignment_group=ticket.assignment_group,
                resolution_action=ticket.resolution_action,
            )
        )

        self.assertTrue(final_obs.done)
        self.assertIsNotNone(final_obs.rubric_reward)
        components = final_obs.last_reward_components

        penalty_total = (
            float(components.get("context_gap_penalty", 0.0))
            + float(components.get("capacity_penalty", 0.0))
            + float(components.get("incident_gap_penalty", 0.0))
        )
        expected_final_reward = clamp_open_unit_interval(float(final_obs.rubric_reward) - penalty_total)

        self.assertAlmostEqual(float(final_obs.reward or 0.0), expected_final_reward, places=9)
        self.assertAlmostEqual(float(components.get("final_reward", 0.0)), expected_final_reward, places=9)
        self.assertEqual(
            components["queue_management_breakdown"]["aggregate"],
            components["queue_management_score"],
        )

    def test_investigation_reward_component_snapshot(self) -> None:
        env, _ = self._single_ticket_env("ticket-074")

        obs2 = env.step(
            HelpdeskTicketAction(
                action_type="investigate",
                tool_name="lookup_internal_routing_note",
            )
        )

        components = obs2.last_reward_components
        snapshot = {
            "reward_kind": components.get("reward_kind"),
            "new_context_revealed": bool(components.get("new_context_revealed")),
            "tool_name": components.get("tool_name"),
        }
        self.assertEqual(
            snapshot,
            {
                "reward_kind": "investigation",
                "new_context_revealed": True,
                "tool_name": "lookup_internal_routing_note",
            },
        )
        self.assertAlmostEqual(float(components.get("final_reward", 0.0)), float(obs2.reward or 0.0), places=9)


if __name__ == "__main__":
    unittest.main()

