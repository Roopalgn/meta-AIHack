from __future__ import annotations

import unittest

import openenv_test_stubs  # noqa: F401

from models import HelpdeskTicketAction, HelpdeskTicketRecord
from server.grader import grade_action


def _ticket(
    *,
    issue_type: str = "billing_license",
    priority: str = "high",
    assignment_group: str = "license_ops",
    resolution_action: str = "fulfill",
) -> HelpdeskTicketRecord:
    return HelpdeskTicketRecord(
        ticket_id="ticket-test",
        title="Test ticket",
        requester="user@example.com",
        description="Synthetic ticket used for deterministic grader tests.",
        issue_type=issue_type,
        priority=priority,
        assignment_group=assignment_group,
        resolution_action=resolution_action,
    )


class GraderUnitTests(unittest.TestCase):
    def test_task_3_exact_match_scores_one(self) -> None:
        ticket = _ticket()
        action = HelpdeskTicketAction(
            issue_type="billing_license",
            priority="high",
            assignment_group="license_ops",
            resolution_action="fulfill",
        )

        score, breakdown = grade_action(action, ticket, task_id=3)

        self.assertAlmostEqual(score, 1.0)
        self.assertEqual(
            breakdown,
            {
                "issue_type": 1.0,
                "priority": 1.0,
                "assignment_group": 1.0,
                "resolution_action": 1.0,
            },
        )

    def test_unknown_task_id_raises(self) -> None:
        ticket = _ticket()
        action = HelpdeskTicketAction(issue_type="billing_license")

        with self.assertRaisesRegex(ValueError, "Unsupported task_id"):
            grade_action(action, ticket, task_id=99)

    def test_issue_type_partial_credit_only_for_known_similarity_pair(self) -> None:
        ticket = _ticket(issue_type="billing_license")
        action = HelpdeskTicketAction(issue_type="service_request")

        score, breakdown = grade_action(action, ticket, task_id=1)

        self.assertAlmostEqual(score, 0.4)
        self.assertEqual(breakdown, {"issue_type": 0.4})

    def test_unrelated_issue_type_gets_zero_not_fuzzy_credit(self) -> None:
        ticket = _ticket(issue_type="onboarding")
        action = HelpdeskTicketAction(issue_type="spam_phishing")

        score, breakdown = grade_action(action, ticket, task_id=1)

        self.assertAlmostEqual(score, 0.0)
        self.assertEqual(breakdown, {"issue_type": 0.0})

    def test_priority_scoring_uses_defined_proximity_table(self) -> None:
        ticket = _ticket(priority="critical")
        action = HelpdeskTicketAction(issue_type="billing_license", priority="high")

        score, breakdown = grade_action(action, ticket, task_id=2)

        self.assertAlmostEqual(breakdown["issue_type"], 1.0)
        self.assertAlmostEqual(breakdown["priority"], 0.6)
        self.assertAlmostEqual(score, 0.84)

    def test_task_2_weights_apply_as_documented(self) -> None:
        ticket = _ticket(priority="high")
        action = HelpdeskTicketAction(issue_type="billing_license", priority="medium")

        score, breakdown = grade_action(action, ticket, task_id=2)

        self.assertEqual(breakdown, {"issue_type": 1.0, "priority": 0.5})
        self.assertAlmostEqual(score, 0.8)

    def test_assignment_group_is_exact_match_only(self) -> None:
        ticket = _ticket()
        action = HelpdeskTicketAction(
            issue_type="billing_license",
            priority="high",
            assignment_group="service_desk",
            resolution_action="fulfill",
        )

        score, breakdown = grade_action(action, ticket, task_id=3)

        self.assertEqual(breakdown["assignment_group"], 0.0)
        self.assertAlmostEqual(score, 0.75)

    def test_resolution_action_is_exact_match_only(self) -> None:
        ticket = _ticket()
        action = HelpdeskTicketAction(
            issue_type="billing_license",
            priority="high",
            assignment_group="license_ops",
            resolution_action="assign",
        )

        score, breakdown = grade_action(action, ticket, task_id=3)

        self.assertEqual(breakdown["resolution_action"], 0.0)
        self.assertAlmostEqual(score, 0.8)


if __name__ == "__main__":
    unittest.main()
