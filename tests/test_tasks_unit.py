from __future__ import annotations

import io
import unittest
from unittest import mock

import openenv_test_stubs  # noqa: F401

from models import HelpdeskTicketRecord
from server import tasks as task_module
from server.tasks import TASKS, get_task_definition, load_dataset
from vocabulary import TASK_IDS


class TasksAndDatasetUnitTests(unittest.TestCase):
    def test_task_ids_match_frozen_contract(self) -> None:
        self.assertEqual(tuple(TASKS.keys()), TASK_IDS)

    def test_task_allowed_fields_match_expected_ladder(self) -> None:
        self.assertEqual(get_task_definition(1)["allowed_fields"], ["issue_type"])
        self.assertEqual(
            get_task_definition(2)["allowed_fields"], ["issue_type", "priority"]
        )
        self.assertEqual(
            get_task_definition(3)["allowed_fields"],
            [
                "issue_type",
                "priority",
                "assignment_group",
                "resolution_action",
            ],
        )

    def test_invalid_task_id_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported task_id"):
            get_task_definition(0)

    def test_load_dataset_returns_valid_records(self) -> None:
        dataset = load_dataset()

        self.assertEqual(len(dataset), 45)
        self.assertTrue(all(isinstance(record, HelpdeskTicketRecord) for record in dataset))

    def test_dataset_ticket_ids_are_unique(self) -> None:
        dataset = load_dataset()
        ticket_ids = [record.ticket_id for record in dataset]

        self.assertEqual(len(ticket_ids), len(set(ticket_ids)))

    def test_related_ticket_ids_reference_existing_records(self) -> None:
        dataset = load_dataset()
        ticket_ids = {record.ticket_id for record in dataset}

        missing_links = [
            record.related_ticket_id
            for record in dataset
            if record.related_ticket_id is not None
            and record.related_ticket_id not in ticket_ids
        ]

        self.assertEqual(missing_links, [])

    def test_dataset_covers_all_defined_issue_types(self) -> None:
        dataset = load_dataset()
        issue_types = {record.issue_type for record in dataset}

        self.assertEqual(
            issue_types,
            {
                "application_support",
                "billing_license",
                "feature_request",
                "general_inquiry",
                "identity_access",
                "onboarding",
                "security_compliance",
                "service_request",
                "spam_phishing",
            },
        )

    def test_load_dataset_accepts_utf8_bom(self) -> None:
        sample = (
            b"\xef\xbb\xbf"
            b"["
            b"{"
            b'"ticket_id":"ticket-bom",'
            b'"title":"BOM test",'
            b'"requester":"user@example.com",'
            b'"description":"Dataset loader should tolerate UTF-8 BOM.",'
            b'"issue_type":"general_inquiry",'
            b'"priority":"low",'
            b'"assignment_group":"service_desk",'
            b'"resolution_action":"acknowledge",'
            b'"ambiguity_note":null,'
            b'"related_ticket_id":null'
            b"}"
            b"]"
        )

        def fake_open(self, mode="r", encoding=None):  # type: ignore[no-untyped-def]
            return io.TextIOWrapper(io.BytesIO(sample), encoding=encoding)

        with mock.patch.object(task_module.Path, "open", fake_open):
            dataset = load_dataset()

        self.assertEqual([record.ticket_id for record in dataset], ["ticket-bom"])


if __name__ == "__main__":
    unittest.main()
