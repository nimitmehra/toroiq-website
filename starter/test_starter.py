import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from run import MARKETS, build


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path(__file__).with_name("config.example.json").read_text())

    def test_all_markets_and_references(self):
        for market in MARKETS:
            with self.subTest(market=market):
                self.config["market"] = market
                graph, queue = build(self.config)
                ids = {node["id"] for node in graph["nodes"]}
                sources = {source["id"] for source in graph["sources"]}
                self.assertEqual(len(ids), len(graph["nodes"]))
                for edge in graph["edges"]:
                    self.assertIn(edge["from"], ids)
                    self.assertIn(edge["to"], ids)
                    self.assertTrue(set(edge["evidence_ids"]) <= sources)
                self.assertEqual(len(queue["items"]), 1)
                self.assertFalse(graph["cadence"]["active"])
                self.assertEqual(graph["mode"], "demo")

    def test_rule_boundary_and_no_match(self):
        for threshold, count in [(12, 1), (13, 0), (0, 1)]:
            self.config["review_rule"]["threshold"] = threshold
            self.assertEqual(len(build(self.config)[1]["items"]), count)

    def test_invalid_config_fails_closed(self):
        for key, value in [("mode", "live"), ("schema_version", "2"), ("market", "unknown"), ("market", []), ("cadence", "hourly"), ("research_question", " "), ("research_question", "x" * 241), ("review_rule", {})]:
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                build(config)
        for threshold in [True, -1, "10", float("nan"), float("inf")]:
            self.config["review_rule"]["threshold"] = threshold
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                build(self.config)

    def test_no_config_mutation_and_stable_review_id(self):
        original = copy.deepcopy(self.config)
        first = build(self.config)[1]
        self.assertEqual(first, build(self.config)[1])
        self.assertEqual(self.config, original)

    def test_cli_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "output"
            command = [sys.executable, str(Path(__file__).with_name("run.py")), "--output", str(target)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            before = (target / "graph.json").read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            self.assertEqual(before, (target / "graph.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
