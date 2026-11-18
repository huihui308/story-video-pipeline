"""Behavioural tests for scripts/project_state.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_state.py"

EXPECTED_DIRS = (
    "writing-pack",
    "audio",
    "characters",
    "images/references",
    "images/generated",
    "review",
    "renders",
)


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, **(env or {})},
    )


class InitTests(unittest.TestCase):
    def test_init_creates_directories_and_valid_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            result = run("init", str(project), "--title", "九子夺嫡", "--host", "dsh")
            self.assertEqual(result.returncode, 0, result.stderr)

            for relative in EXPECTED_DIRS:
                self.assertTrue((project / relative).is_dir(), relative)

            state = json.loads((project / "PROJECT_STATE.json").read_text(encoding="utf-8"))
            self.assertEqual(state["schema_version"], 1)
            self.assertEqual(state["current_stage"], "START")
            self.assertEqual(state["host"]["name"], "dsh")
            self.assertEqual(state["host"]["capabilities"]["local_files"], True)
            self.assertIn("run mode", state["pending_request"])
            self.assertIn("aspect ratio", state["pending_request"])

    def test_host_matrix_defaults(self):
        cases = {
            "dsh": True,
            "opencode": True,
            "codex": True,
            "workbuddy": False,
            "other": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            for host, expected in cases.items():
                project = Path(tmp) / host
                self.assertEqual(
                    run("init", str(project), "--title", host, "--host", host).returncode, 0
                )
                state = json.loads((project / "PROJECT_STATE.json").read_text(encoding="utf-8"))
                self.assertEqual(state["host"]["capabilities"]["local_files"], expected, host)

    def test_local_files_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            forced_on = Path(tmp) / "on"
            run("init", str(forced_on), "--title", "t", "--host", "workbuddy", "--local-files")
            state = json.loads((forced_on / "PROJECT_STATE.json").read_text(encoding="utf-8"))
            self.assertTrue(state["host"]["capabilities"]["local_files"])

            forced_off = Path(tmp) / "off"
            run("init", str(forced_off), "--title", "t", "--host", "dsh", "--no-local-files")
            state = json.loads((forced_off / "PROJECT_STATE.json").read_text(encoding="utf-8"))
            self.assertFalse(state["host"]["capabilities"]["local_files"])

    def test_init_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            run("init", str(project), "--title", "t", "--host", "dsh")
            self.assertEqual(run("init", str(project), "--title", "t", "--host", "dsh").returncode, 2)


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name) / "project"
        run("init", str(self.project), "--title", "九子夺嫡", "--host", "dsh")
        self.state_path = self.project / "PROJECT_STATE.json"

    def tearDown(self):
        self._tmp.cleanup()

    def mutate(self, **changes):
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        state.update(changes)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    def assert_invalid(self, fragment: str):
        result = run("validate", str(self.state_path))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(fragment, result.stderr)

    def test_valid_state(self):
        result = run("validate", str(self.state_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_unknown_stage(self):
        self.mutate(current_stage="EDITING")
        self.assert_invalid("current_stage")

    def test_unknown_status(self):
        self.mutate(stage_status="已验收")
        self.assert_invalid("stage_status")

    def test_boolean_schema_version(self):
        self.mutate(schema_version=True)
        self.assert_invalid("schema_version")

    def test_missing_capability(self):
        state = self.mutate()
        del state["host"]["capabilities"]["shell"]
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.assert_invalid("capabilities missing keys")

    def test_non_boolean_capability(self):
        state = self.mutate()
        state["host"]["capabilities"]["tts"] = "yes"
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.assert_invalid("booleans")

    def test_bad_timestamp(self):
        self.mutate(updated_at="yesterday")
        self.assert_invalid("ISO-8601")

    def test_relative_project_root(self):
        self.mutate(project_root="project")
        self.assert_invalid("absolute")

    def test_stage_history_entry_type(self):
        self.mutate(stage_history=["BRIEF"])
        self.assert_invalid("stage_history")


class RepairAndSummaryTests(unittest.TestCase):
    def test_repair_after_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "original"
            run("init", str(original), "--title", "九子夺嫡", "--host", "dsh")
            moved = Path(tmp) / "moved"
            original.rename(moved)
            state = moved / "PROJECT_STATE.json"

            broken = run("validate", str(state))
            self.assertEqual(broken.returncode, 1)
            self.assertIn("repair", broken.stderr)

            repaired = run("repair", str(state))
            self.assertEqual(repaired.returncode, 0, repaired.stderr)
            self.assertIn("REPAIRED", repaired.stdout)

            self.assertEqual(run("validate", str(state)).returncode, 0)
            data = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(Path(data["project_root"]), moved.resolve())

    def test_repair_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            run("init", str(project), "--title", "t", "--host", "dsh")
            state = project / "PROJECT_STATE.json"
            second = run("repair", str(state))
            self.assertEqual(second.returncode, 0)
            self.assertIn("OK", second.stdout)

    def test_summary_reports_none_next_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            run("init", str(project), "--title", "九子夺嫡", "--host", "dsh")
            state_path = project / "PROJECT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["next_stage"] = None
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

            result = run("summary", str(state_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Host: dsh", result.stdout)
            self.assertIn("(none)", result.stdout)
            self.assertNotIn("None", result.stdout)

    def test_utf8_output_under_gbk_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            run("init", str(project), "--title", "九子夺嫡", "--host", "dsh")
            state = project / "PROJECT_STATE.json"
            result = run("summary", str(state), env={"PYTHONIOENCODING": "gbk"})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("九子夺嫡", result.stdout)
            self.assertIn("进行中", result.stdout)


if __name__ == "__main__":
    unittest.main()
