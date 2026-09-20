import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_csv.py"


class PrepareCsvTests(unittest.TestCase):
    def run_tool(self, source_text, *extra_args):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = root / "source.csv"
        output = root / "review.csv"
        source.write_text(source_text, encoding="utf-8")
        before = source.read_bytes()
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(source),
                "--output",
                str(output),
                *extra_args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(source.read_bytes(), before)
        return result, output

    def read_rows(self, output):
        with output.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_normalizes_common_headings(self):
        result, output = self.run_tool(
            "Description,Content,Created,Audio URL\n"
            'Plan,"Book the venue",2026-09-01,https://example.test/1\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        rows = self.read_rows(output)
        self.assertEqual(report["rows_written"], 1)
        self.assertEqual(report["unique_ids"], 1)
        self.assertEqual(rows[0]["title"], "Plan")
        self.assertEqual(rows[0]["transcript"], "Book the venue")
        self.assertEqual(rows[0]["decision"], "Pending")
        self.assertTrue(rows[0]["memo_id"].startswith("vm_"))

    def test_explicit_column_overrides(self):
        result, output = self.run_tool(
            "Memo Key,Memo Heading,Memo Words,When\n"
            "abc-1,Idea,Write an outline,2026-09-02\n",
            "--id-column",
            "Memo Key",
            "--title-column",
            "Memo Heading",
            "--transcript-column",
            "Memo Words",
            "--date-column",
            "When",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        row = self.read_rows(output)[0]
        self.assertEqual(row["memo_id"], "abc-1")
        self.assertEqual(row["recorded_at"], "2026-09-02")

    def test_missing_transcript_column_fails(self):
        result, output = self.run_tool("Description,Created\nPlan,2026-09-01\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())
        error = json.loads(result.stderr)
        self.assertIn("transcript/content", error["error"])

    def test_duplicate_source_ids_become_unique(self):
        result, output = self.run_tool(
            "id,content\nsame,First memo\nsame,Second memo\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = self.read_rows(output)
        self.assertEqual([row["memo_id"] for row in rows], ["same", "same-2"])

    def test_refuses_to_overwrite_source(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        source = Path(temp.name) / "source.csv"
        source.write_text("content\nHello\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(source),
                "--output",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must differ", result.stderr)


if __name__ == "__main__":
    unittest.main()
