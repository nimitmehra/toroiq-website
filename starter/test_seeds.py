import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from seed import ROOT, MARKETS, initialize, validate_graph


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "seed.config.example.json").read_text())

    def test_all_packs(self):
        for market in MARKETS:
            self.config["market"] = market
            graph, queue, workspace = initialize(self.config, date(2026, 9, 11))
            self.assertGreaterEqual(len(graph["nodes"]), 10)
            self.assertGreaterEqual(len(graph["edges"]), 9)
            self.assertFalse(workspace["schedule_active"])
            self.assertTrue(all(not n["observations"] for n in graph["nodes"]))
            self.assertTrue(any(i["kind"] == "hypothesis_review" for i in queue["items"]))

    def test_every_focus_and_hop_depth(self):
        for market in MARKETS:
            self.config["market"] = market
            all_nodes = initialize(self.config)[0]["nodes"]
            for node in all_nodes:
                for depth in (0, 1, 2):
                    config = dict(self.config, focus=[node["id"]], neighbor_hops=depth)
                    graph, _, _ = initialize(config)
                    validate_graph(graph)
                    self.assertIn(node["id"], [n["id"] for n in graph["nodes"]])
                    if depth == 0:
                        self.assertEqual(len(graph["nodes"]), 1)
                        self.assertEqual(graph["edges"], [])

    def test_unknown_focus_and_invalid_config(self):
        for key, value in [("focus", ["nse:UNKNOWN"]), ("neighbor_hops", True), ("neighbor_hops", 3), ("mode", "live"), ("market", "other"), ("seed_version", "99"), ("research_question", " ")]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                initialize(dict(self.config, **{key: value}))

    def test_source_age(self):
        _, queue, _ = initialize(self.config, date(2027, 9, 11))
        self.assertTrue(any(x["kind"] == "source_review_due" for x in queue["items"]))

    def test_catalog_and_project_manifest_match(self):
        catalog = json.loads((ROOT / "seeds/index.json").read_text())
        projects = json.loads((ROOT.parent / "projects.json").read_text())
        for item in catalog["packs"]:
            self.config["market"] = item["market"]
            graph, _, _ = initialize(self.config)
            self.assertEqual(item["node_count"], len(graph["nodes"]))
            self.assertEqual(item["edge_count"], len(graph["edges"]))
            self.assertEqual(item["source_count"], len(graph["sources"]))
            self.assertEqual(item["documented_count"], sum(e["status"] == "documented" for e in graph["edges"]))
            self.assertEqual(item["hypothesis_count"], sum(e["status"] == "hypothesis" for e in graph["edges"]))
            self.assertEqual({x["id"] for x in item["focus_options"]}, {n["id"] for n in graph["nodes"]})
            project = next(p for p in projects["projects"] if p["id"] == item["market"])
            self.assertEqual(project["seed"]["nodes"], item["node_count"])
            self.assertEqual(project["seed"]["url"], item["url"])

    def test_dangling_and_duplicate_records_fail(self):
        base = initialize(self.config)[0]
        graph = copy.deepcopy(base)
        graph["edges"][0]["to"] = "missing"
        with self.assertRaises(ValueError):
            validate_graph(graph)
        graph = copy.deepcopy(base)
        graph["nodes"].append(copy.deepcopy(graph["nodes"][0]))
        with self.assertRaises(ValueError):
            validate_graph(graph)
        graph = copy.deepcopy(base)
        graph["edges"][0]["source_ids"] = ["missing"]
        with self.assertRaises(ValueError):
            validate_graph(graph)

    def test_no_overwrite_and_no_input_mutation(self):
        before = copy.deepcopy(self.config)
        initialize(self.config)
        self.assertEqual(before, self.config)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "workspace"
            cmd = [sys.executable, str(ROOT / "seed.py"), "--output", str(output)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            original = (output / "graph.json").read_bytes()
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 1)
            self.assertEqual(original, (output / "graph.json").read_bytes())
            self.assertEqual(len(list(output.iterdir())), 5)


if __name__ == "__main__":
    unittest.main()
