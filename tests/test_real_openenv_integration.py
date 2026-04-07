from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE_PACKAGES = os.path.join(REPO_ROOT, ".venv", "Lib", "site-packages")
if SITE_PACKAGES not in sys.path:
    sys.path.insert(0, SITE_PACKAGES)

for module_name in list(sys.modules):
    if module_name == "openenv" or module_name.startswith("openenv."):
        del sys.modules[module_name]
for module_name in list(sys.modules):
    if module_name in {"models", "server.app", "server.environment", "client"}:
        del sys.modules[module_name]

try:
    from starlette.testclient import TestClient
    from server.app import app

    REAL_OPENENV_AVAILABLE = True
    IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - only used for skip messaging
    REAL_OPENENV_AVAILABLE = False
    IMPORT_ERROR = exc


@unittest.skipUnless(
    REAL_OPENENV_AVAILABLE,
    f"real OpenEnv stack unavailable: {IMPORT_ERROR}",
)
class RealOpenEnvIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_redirects_to_web(self) -> None:
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/web")

    def test_grader_endpoint_scores_known_action(self) -> None:
        response = self.client.post(
            "/grader",
            json={
                "task_id": 3,
                "ticket_id": "ticket-002",
                "action": {
                    "issue_type": "identity_access",
                    "priority": "high",
                    "assignment_group": "service_desk",
                    "resolution_action": "fulfill",
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["score"], 1.0)
        self.assertEqual(payload["breakdown"]["issue_type"], 1.0)

    def test_baseline_endpoint_runs_episode(self) -> None:
        response = self.client.get("/baseline", params={"task_id": 3, "seed": 42})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["task_id"], 3)
        self.assertGreater(payload["step_count"], 0)
        self.assertIn("steps", payload)
        self.assertIsInstance(payload["steps"], list)

    def test_websocket_round_trip_reset_state_step(self) -> None:
        with self.client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "reset", "data": {"task_id": 1, "seed": 42}})
            reset_message = websocket.receive_json()
            self.assertEqual(reset_message["type"], "observation")
            reset_payload = reset_message["data"]
            reset_obs = reset_payload.get("observation", reset_payload)
            self.assertEqual(reset_obs["task_id"], 1)
            self.assertFalse(reset_payload.get("done", reset_obs.get("done", False)))

            websocket.send_json({"type": "state"})
            state_message = websocket.receive_json()
            self.assertEqual(state_message["type"], "state")
            self.assertEqual(state_message["data"]["current_task_id"], 1)

            websocket.send_json(
                {
                    "type": "step",
                    "data": {
                        "issue_type": "billing_license",
                    },
                }
            )
            step_message = websocket.receive_json()
            self.assertEqual(step_message["type"], "observation")
            step_payload = step_message["data"]
            step_obs = step_payload.get("observation", step_payload)
            reward = step_payload.get("reward", step_obs.get("reward"))
            self.assertGreaterEqual(reward, 0.0)
            self.assertLessEqual(reward, 1.0)


if __name__ == "__main__":
    unittest.main()
