"""
Tests for action field validation (Task 4) in HelpdeskTicketRoutingEnvironment.step().

Validates Requirement 7: Step Validates Action Fields Against Task Contract.
"""
from __future__ import annotations

import contextlib
import sys
import os
import unittest
import types as _types

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

from models import HelpdeskTicketAction, HelpdeskTicketObservation
from server.environment import HelpdeskTicketRoutingEnvironment
from server.tasks import TASKS
from vocabulary import ISSUE_TYPES, PRIORITIES, ASSIGNMENT_GROUPS, RESOLUTION_ACTIONS


def _make_env() -> HelpdeskTicketRoutingEnvironment:
    return HelpdeskTicketRoutingEnvironment()


def _task_with_issue_type_only(task_id: int) -> dict:
    task = dict(TASKS[task_id])
    if task_id == 1:
        task["allowed_fields"] = ["issue_type"]
    return task


@contextlib.contextmanager
def _restrict_task_1_fields():
    original_fields = list(TASKS[1]["allowed_fields"])
    TASKS[1]["allowed_fields"] = ["issue_type"]
    try:
        yield
    finally:
        TASKS[1]["allowed_fields"] = original_fields


class TestExtraFieldsPenalty(unittest.TestCase):
    """Requirement 7: step() rejects actions with fields outside the task's allowed_fields."""

    def test_extra_fields_returns_closed_interval_penalty_reward(self) -> None:
        """Task 1 penalties should keep the returned reward inside the unit interval."""
        env = _make_env()
        with _restrict_task_1_fields():
            obs = env.reset(seed=42, task_id=1)

            # Task 1 allowed_fields should NOT include assignment_group
            self.assertNotIn("assignment_group", obs.allowed_fields)

            # Submit an action with an extra field (assignment_group) not in task 1's allowed_fields
            action = HelpdeskTicketAction(
                issue_type=ISSUE_TYPES[0],
                priority=PRIORITIES[0],
                assignment_group=ASSIGNMENT_GROUPS[0],  # extra field
            )
            penalty_obs = env.step(action)

        self.assertIsInstance(penalty_obs, HelpdeskTicketObservation)
        self.assertGreaterEqual(penalty_obs.reward, 0.0)
        self.assertLess(penalty_obs.reward, 1.0)

    def test_extra_fields_advances_ticket_index(self) -> None:
        """Penalty step must advance tickets_processed by 1."""
        env = _make_env()
        with _restrict_task_1_fields():
            obs = env.reset(seed=42, task_id=1)
            self.assertEqual(obs.tickets_processed, 0)

            action = HelpdeskTicketAction(
                issue_type=ISSUE_TYPES[0],
                assignment_group=ASSIGNMENT_GROUPS[0],  # extra field for task 1
            )
            penalty_obs = env.step(action)

        self.assertEqual(penalty_obs.tickets_processed, 1)

    def test_extra_fields_records_score_inside_unit_interval(self) -> None:
        """per_ticket_scores must stay in the unit interval after a penalty step."""
        env = _make_env()
        with _restrict_task_1_fields():
            env.reset(seed=42, task_id=1)

            action = HelpdeskTicketAction(
                issue_type=ISSUE_TYPES[0],
                assignment_group=ASSIGNMENT_GROUPS[0],  # extra field
            )
            env.step(action)

        state = env.state
        self.assertEqual(len(state.per_ticket_scores), 1)
        self.assertGreaterEqual(state.per_ticket_scores[0], 0.0)
        self.assertLess(state.per_ticket_scores[0], 1.0)

    def test_extra_fields_history_entry_has_penalty_reason(self) -> None:
        """History entry for a penalty step must include penalty_reason."""
        env = _make_env()
        with _restrict_task_1_fields():
            env.reset(seed=42, task_id=1)

            action = HelpdeskTicketAction(
                issue_type=ISSUE_TYPES[0],
                assignment_group=ASSIGNMENT_GROUPS[0],  # extra field
            )
            penalty_obs = env.step(action)

        self.assertEqual(len(penalty_obs.history), 1)
        entry = penalty_obs.history[0]
        self.assertIn("penalty_reason", entry)
        self.assertIn("assignment_group", entry["penalty_reason"])
        self.assertGreaterEqual(entry["score"], 0.0)
        self.assertLess(entry["score"], 1.0)

    def test_no_extra_fields_grades_normally(self) -> None:
        """When action fields are within allowed_fields, grading proceeds normally (reward != forced 0.0)."""
        env = _make_env()
        with _restrict_task_1_fields():
            obs = env.reset(seed=42, task_id=1)

            # Build action using only allowed fields
            allowed = obs.allowed_fields
            action_kwargs = {}
            if "issue_type" in allowed:
                action_kwargs["issue_type"] = ISSUE_TYPES[0]
            if "priority" in allowed:
                action_kwargs["priority"] = PRIORITIES[0]

            action = HelpdeskTicketAction(**action_kwargs)
            result_obs = env.step(action)

        # Should be a valid observation; reward may be any value in [0.0, 1.0]
        self.assertIsInstance(result_obs, HelpdeskTicketObservation)
        self.assertIsNotNone(result_obs.reward)
        # No penalty_reason in history
        self.assertEqual(len(result_obs.history), 1)
        self.assertNotIn("penalty_reason", result_obs.history[0])

    def test_action_metadata_is_not_treated_as_extra_field(self) -> None:
        """OpenEnv Action metadata should not trigger the extra-fields penalty."""
        env = _make_env()
        with _restrict_task_1_fields():
            obs = env.reset(seed=42, task_id=1)
            ticket_id = obs.current_ticket["ticket_id"]
            current_ticket = env._tickets_by_id[ticket_id]  # noqa: SLF001 - test-only inspection

            result_obs = env.step(
                HelpdeskTicketAction(
                    issue_type=current_ticket.issue_type,
                    metadata={},
                )
            )

        self.assertEqual(len(result_obs.history), 1)
        self.assertNotIn("penalty_reason", result_obs.history[0])
        self.assertGreater(result_obs.history[0]["score"], 0.0)

    def test_extra_fields_no_exception_raised(self) -> None:
        """Requirement 7.4: extra fields must not raise an unhandled exception."""
        env = _make_env()
        with _restrict_task_1_fields():
            env.reset(seed=42, task_id=1)

            action = HelpdeskTicketAction(
                issue_type=ISSUE_TYPES[0],
                priority=PRIORITIES[0],
                assignment_group=ASSIGNMENT_GROUPS[0],
                resolution_action=RESOLUTION_ACTIONS[0],  # multiple extra fields
            )
            try:
                obs = env.step(action)
            except Exception as exc:  # noqa: BLE001
                self.fail(f"step() raised an unexpected exception: {exc}")

        self.assertIsInstance(obs, HelpdeskTicketObservation)

    def test_extra_fields_done_flag_set_correctly_on_last_ticket(self) -> None:
        """When the penalty step is on the last ticket, done stays True and reward stays episode-level."""
        env = _make_env()
        with _restrict_task_1_fields():
            obs = env.reset(seed=42, task_id=1)
            queue_size = obs.queue_size
            tickets_by_id = env._tickets_by_id  # noqa: SLF001 - test-only inspection

            # Process all tickets except the last one normally
            for _ in range(queue_size - 1):
                current_ticket_id = obs.current_ticket["ticket_id"]
                current_ticket = tickets_by_id[current_ticket_id]
                obs = env.step(HelpdeskTicketAction(issue_type=current_ticket.issue_type))

            # Now trigger penalty on the last ticket
            current_ticket_id = obs.current_ticket["ticket_id"]
            current_ticket = tickets_by_id[current_ticket_id]
            action = HelpdeskTicketAction(
                issue_type=current_ticket.issue_type,
                assignment_group=ASSIGNMENT_GROUPS[0],  # extra field
            )
            final_obs = env.step(action)

        self.assertTrue(final_obs.done)
        self.assertGreater(final_obs.reward, 0.0)
        self.assertLess(final_obs.reward, 1.0)
        self.assertGreater(env.state.total_reward, 0.0)
        self.assertLess(env.state.total_reward, 1.0)

    def test_missing_required_submit_fields_use_consistent_penalty_path(self) -> None:
        env = _make_env()
        obs = env.reset(seed=42, task_id=1)

        # Task 1 requires full routing; providing only issue_type should be penalized.
        penalty_obs = env.step(HelpdeskTicketAction(issue_type=ISSUE_TYPES[0]))

        self.assertIsInstance(penalty_obs, HelpdeskTicketObservation)
        self.assertEqual(penalty_obs.tickets_processed, 1)
        self.assertIn("penalty_reason", penalty_obs.history[0])
        self.assertIn("missing_submit_fields", penalty_obs.history[0]["penalty_reason"])
        self.assertEqual(penalty_obs.last_reward_components.get("invalid_action"), True)

    def test_investigate_without_tool_name_penalized_not_raised(self) -> None:
        env = _make_env()
        env.reset(seed=42, task_id=1)

        try:
            penalty_obs = env.step(HelpdeskTicketAction(action_type="investigate"))
        except Exception as exc:  # noqa: BLE001
            self.fail(f"Expected penalty observation, but step() raised: {exc}")

        self.assertIsInstance(penalty_obs, HelpdeskTicketObservation)
        self.assertIn("penalty_reason", penalty_obs.history[-1])
        self.assertIn("require tool_name", penalty_obs.history[-1]["penalty_reason"])
        self.assertGreaterEqual(penalty_obs.reward, 0.0)
        self.assertLessEqual(penalty_obs.reward, 1.0)

    def test_open_incident_with_submit_fields_penalized_consistently(self) -> None:
        env = _make_env()
        env.reset(seed=42, task_id=3)

        penalty_obs = env.step(
            HelpdeskTicketAction(
                action_type="open_incident",
                issue_type="identity_access",
            )
        )

        self.assertIn("penalty_reason", penalty_obs.history[-1])
        self.assertIn("cannot include submit fields", penalty_obs.history[-1]["penalty_reason"])
        self.assertEqual(penalty_obs.last_reward_components.get("reward_kind"), "step_penalty")
        self.assertEqual(penalty_obs.last_reward_components.get("invalid_action"), True)


if __name__ == "__main__":
    unittest.main()
