#!/usr/bin/env python3
"""Create a customer-owned workspace from a versioned structural research seed.

Offline only: no model calls, web requests, schedule installation or notifications.
"""
import argparse
import copy
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
MARKETS = ("macro", "nse", "us", "crypto")
SCHEMA_VERSION = "0.2.0"
SEED_VERSION = "0.1.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identifiers(records, label):
    require(isinstance(records, list) and records, label + " must be a nonempty list")
    require(all(isinstance(x, dict) and isinstance(x.get("id"), str) and x["id"] for x in records), label + " need string IDs")
    ids = [x["id"] for x in records]
    require(len(ids) == len(set(ids)), "Duplicate " + label + " IDs")
    return set(ids)


def validate_graph(graph):
    require(isinstance(graph, dict), "Graph must be an object")
    require(graph.get("schema_version") == SCHEMA_VERSION and graph.get("seed_version") == SEED_VERSION, "Unsupported seed/schema version")
    require(graph.get("mode") == "seed" and graph.get("market") in MARKETS, "Invalid seed mode/market")
    for key in ("title", "scope", "license"):
        require(isinstance(graph.get(key), str) and graph[key].strip(), "Missing " + key)
    date.fromisoformat(graph["reviewed_at"])
    require(bool(graph.get("limitations")) and isinstance(graph["limitations"], list), "Missing limitations")
    require(isinstance(graph.get("update_plan"), dict), "Missing update plan")
    nodes = identifiers(graph.get("nodes"), "node")
    sources = identifiers(graph.get("sources"), "source")
    # A focused graph can legitimately contain no edges.
    require(isinstance(graph.get("edges"), list), "Edges must be a list")
    if graph["edges"]:
        identifiers(graph["edges"], "edge")
    for node in graph["nodes"]:
        require(node.get("observations") == [], "Structural seeds must not contain unreviewed numerical observations")
        require(all(isinstance(node.get(k), str) and node[k].strip() for k in ("type", "label", "research_question")), "Invalid node metadata")
    for record in graph["nodes"] + graph["edges"]:
        refs = record.get("source_ids")
        require(isinstance(refs, list) and refs and all(isinstance(x, str) and x in sources for x in refs), "Missing or unresolved source reference")
    pairs = set()
    for edge in graph["edges"]:
        require(edge.get("from") in nodes and edge.get("to") in nodes, "Dangling edge")
        require(edge["from"] != edge["to"], "Self-edge not supported")
        require(edge.get("status") in ("documented", "hypothesis"), "Invalid relationship status")
        require(all(isinstance(edge.get(k), str) and edge[k].strip() for k in ("relation", "mechanism", "research_question")), "Missing relationship explanation")
        date.fromisoformat(edge["reviewed_at"])
        pair = (edge["from"], edge["to"], edge["relation"])
        require(pair not in pairs, "Duplicate relationship")
        pairs.add(pair)
    for source in graph["sources"]:
        require(all(isinstance(source.get(k), str) and source[k].strip() for k in ("title", "url", "publisher", "locator", "basis")), "Missing source provenance")
        parsed = urlsplit(source["url"])
        require(parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username, "Invalid source URL")
        date.fromisoformat(source["reviewed_at"])
        require(type(source.get("review_after_days")) is int and source["review_after_days"] > 0, "Invalid source review interval")


def validate_config(config):
    require(isinstance(config, dict), "Configuration must be an object")
    keys = {"schema_version", "seed_version", "mode", "market", "cadence", "research_question", "focus", "neighbor_hops"}
    require(set(config) == keys, "Configuration requires exactly: " + ", ".join(sorted(keys)))
    require(config["schema_version"] == SCHEMA_VERSION and config["seed_version"] == SEED_VERSION, "Unsupported seed/schema version")
    require(config["mode"] == "seed" and config["market"] in MARKETS, "Use seed mode and a supported market")
    require(config["cadence"] in ("on-demand", "daily", "weekly"), "Invalid cadence")
    require(isinstance(config["research_question"], str) and 1 <= len(config["research_question"].strip()) <= 240, "Research question must be 1–240 nonblank characters")
    require(isinstance(config["focus"], list) and all(isinstance(x, str) and x for x in config["focus"]), "focus must be a list of node IDs")
    require(len(config["focus"]) == len(set(config["focus"])), "Duplicate focus IDs")
    require(type(config["neighbor_hops"]) is int and 0 <= config["neighbor_hops"] <= 2, "neighbor_hops must be 0, 1 or 2")


def initialize(config, today=None):
    validate_config(config)
    today = today or date.today()
    graph = json.loads((ROOT / "seeds" / (config["market"] + ".json")).read_text(encoding="utf-8"))
    validate_graph(graph)
    selected = set(config["focus"])
    all_ids = {n["id"] for n in graph["nodes"]}
    require(selected <= all_ids, "Unknown focus IDs: " + ", ".join(sorted(selected - all_ids)))
    if selected:
        for _ in range(config["neighbor_hops"]):
            expanded = set(selected)
            for edge in graph["edges"]:
                if edge["from"] in selected or edge["to"] in selected:
                    expanded.update((edge["from"], edge["to"]))
            selected = expanded
        graph["nodes"] = [n for n in graph["nodes"] if n["id"] in selected]
        graph["edges"] = [e for e in graph["edges"] if e["from"] in selected and e["to"] in selected]
        used = {ref for record in graph["nodes"] + graph["edges"] for ref in record["source_ids"]}
        graph["sources"] = [s for s in graph["sources"] if s["id"] in used]
    validate_graph(graph)
    items = []
    for source in graph["sources"]:
        age = (today - date.fromisoformat(source["reviewed_at"])).days
        items.append({"id": "source:" + source["id"], "kind": "source_review_due" if age >= source["review_after_days"] else "initial_source_check", "source_ids": [source["id"]], "reason": "Check original context and newer disclosures before relying on this seed.", "days_since_review": age})
    for edge in graph["edges"]:
        if edge["status"] == "hypothesis":
            items.append({"id": "hypothesis:" + edge["id"], "kind": "hypothesis_review", "edge_id": edge["id"], "source_ids": edge["source_ids"], "reason": edge["research_question"]})
    queue = {"schema_version": SCHEMA_VERSION, "mode": "seed", "as_of": today.isoformat(), "items": items,
             "notice": "Initial research tasks, not detected market changes, verified causality or investment signals. No notifications sent."}
    workspace = copy.deepcopy(config)
    workspace["schedule_active"] = False
    workspace["initialized_at"] = today.isoformat()
    return graph, queue, workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "seed.config.example.json")
    parser.add_argument("--output", type=Path, help="New directory only; existing directories are rejected")
    parser.add_argument("--validate-only", action="store_true", help="Validate all four bundled seeds without writing files")
    args = parser.parse_args()
    try:
        if args.validate_only:
            for market in MARKETS:
                graph = json.loads((ROOT / "seeds" / (market + ".json")).read_text(encoding="utf-8"))
                validate_graph(graph)
                print(f"PASS {market}: {len(graph['nodes'])} nodes, {len(graph['edges'])} relationships")
            return 0
        require(args.output is not None, "--output is required unless using --validate-only")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        graph, queue, workspace = initialize(config)
        args.output.mkdir(parents=True, exist_ok=False)
        for name, data in (("graph.json", graph), ("review-queue.json", queue), ("workspace.json", workspace), ("research.config.json", config)):
            with (args.output / name).open("x", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, allow_nan=False)
                handle.write("\n")
        with (args.output / "UPDATE_GUIDE.md").open("x", encoding="utf-8") as handle:
            handle.write((ROOT / "UPDATE_GUIDE.md").read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1
    print(f"Created {args.output}: {len(graph['nodes'])} nodes, {len(graph['edges'])} relationships.")
    print("Source-linked structural seed. No live data fetched, model called or schedule activated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
