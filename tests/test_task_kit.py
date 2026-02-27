import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "task-kit"


class TaskKitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name) / "handbook"

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess:
        cmd = ["python3", str(SCRIPTS / script), *args, "--root", str(self.root)]
        return subprocess.run(cmd, check=True, capture_output=True, text=True)

    def test_create_and_info(self):
        create = self.run_script("task_create.py", "ohmyopenclaw", "build inbox plugin", "--assignee", "forge")
        task_file = pathlib.Path(create.stdout.strip())
        self.assertTrue(task_file.exists())

        info = self.run_script("task_info.py", "ohmyopenclaw", "--json")
        self.assertIn('"assignee": "forge"', info.stdout)
        self.assertIn('"status": "open"', info.stdout)

    def test_archive(self):
        create = self.run_script("task_create.py", "ohmyopenclaw", "archive me", "--assignee", "forge")
        task_file = pathlib.Path(create.stdout.strip())
        task_dir = task_file.parent

        archived = self.run_script("task_archive.py", "ohmyopenclaw", task_dir.name)
        archive_dir = pathlib.Path(archived.stdout.strip())
        self.assertTrue(archive_dir.exists())
        self.assertFalse(task_dir.exists())

    def test_assignment_create(self):
        create = self.run_script("task_create.py", "ohmyopenclaw", "assign me", "--assignee", "forge")
        task_file = pathlib.Path(create.stdout.strip())

        assignment = self.run_script(
            "assignment_create.py",
            "2026-02-26-assign-me",
            "--to",
            "forge",
            "--from-agent",
            "syla",
            "--project",
            "ohmyopenclaw",
            "--task-path",
            str(task_file),
            "--priority",
            "high",
            "--summary",
            "test assignment",
        )
        assignment_file = pathlib.Path(assignment.stdout.strip())
        self.assertTrue(assignment_file.exists())
        text = assignment_file.read_text(encoding="utf-8")
        self.assertIn("to: forge", text)
        self.assertIn("status: assigned", text)
        self.assertIn("summary: test assignment", text)


if __name__ == "__main__":
    unittest.main()
