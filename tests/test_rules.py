import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agi_benchmark.core import score


class RuleTests(unittest.TestCase):
    def evaluate(self, *args):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "benchmark.py"), *args, "--format", "json"], capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def test_original_scores_and_ascii_case_matching(self):
        expected = {"model-xyz": 0, "model-a": 33, "model-gi": 67, "model-agi": 100, "AAAgggIII": 100, "İ": 0}
        for name, value in expected.items():
            self.assertEqual(score(name), value)

    def test_exact_fraction_and_rounding(self):
        code, report = self.evaluate("model-gi", "--precision", "2")
        self.assertEqual(code, 0)
        row = report["results"][0]
        self.assertEqual(row["score"], 66.67)
        self.assertEqual(row["details"]["ratio"], {"numerator": 2, "denominator": 3})
        self.assertEqual(report["rules"]["profile"], "custom")

    def test_case_and_target_overrides(self):
        _, report = self.evaluate("aGi", "--letters", "AGI", "--case-sensitive")
        self.assertEqual(report["results"][0]["score"], 33)
        self.assertEqual(report["results"][0]["details"]["matched_letters"], ["G"])

    def test_invalid_rules(self):
        for args, error in [(('--letters', 'aA'), 'duplicate_letters'), (('--letters', '你好'), 'invalid_letters'), (('--precision', '9'), 'invalid_arguments')]:
            code, report = self.evaluate("model-agi", *args)
            self.assertEqual(code, 2)
            self.assertEqual(report["error"]["code"], error)

    def test_cli_overrides_config_and_boolean_type_is_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rules.json"
            path.write_text(json.dumps({"benchmark": "agi-achievement-rate", "rules": {"precision": 2}}), encoding="utf-8")
            code, report = self.evaluate("model-gi", "--config", str(path), "--precision", "0")
            self.assertEqual(code, 0)
            self.assertEqual(report["results"][0]["score"], 67)
            self.assertEqual(report["rules"]["profile"], "standard")
            path.write_text(json.dumps({"benchmark": "agi-achievement-rate", "rules": {"case_sensitive": "false"}}), encoding="utf-8")
            code, report = self.evaluate("model-agi", "--config", str(path))
            self.assertEqual(code, 2)
            self.assertEqual(report["error"]["code"], "invalid_boolean")


if __name__ == "__main__":
    unittest.main()
