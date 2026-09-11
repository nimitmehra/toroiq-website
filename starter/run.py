#!/usr/bin/env python3
"""Offline, fictional graph demo. No network, model calls or scheduling."""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

MARKETS = {
    "macro": ("Example freight index", "Example importer", "Higher freight costs could pressure the importer's margins."),
    "nse": ("Example input-cost index", "Example Indian manufacturer", "Higher input costs could pressure the manufacturer's margins."),
    "us": ("Example customer spending index", "Example US supplier", "Higher customer spending could create demand for the supplier."),
    "crypto": ("Example network activity index", "Example protocol", "Higher activity could indicate adoption, but incentives must be checked."),
}


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object.")
    allowed = {"schema_version", "mode", "market", "cadence", "research_question", "review_rule"}
    if set(config) != allowed:
        raise ValueError("Configuration must contain exactly: " + ", ".join(sorted(allowed)))
    if config["schema_version"] != "0.1.0" or config["mode"] != "demo":
        raise ValueError("This starter supports only schema_version 0.1.0 and mode demo. It cannot fetch live data.")
    if not isinstance(config["market"], str) or config["market"] not in MARKETS:
        raise ValueError("market must be macro, nse, us or crypto.")
    if config["cadence"] not in ("on-demand", "daily", "weekly"):
        raise ValueError("cadence must be on-demand, daily or weekly; it does not activate a schedule.")
    if not isinstance(config["research_question"], str) or not 1 <= len(config["research_question"].strip()) <= 240:
        raise ValueError("research_question must be 1–240 characters.")
    rule = config["review_rule"]
    if not isinstance(rule, dict) or set(rule) != {"field", "operator", "threshold"}:
        raise ValueError("review_rule requires field, operator and threshold.")
    threshold = rule["threshold"]
    if rule["field"] != "change_pct" or rule["operator"] != "gte":
        raise ValueError("The demo rule supports only change_pct with operator gte (signed increase, not absolute movement).")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be a finite, nonnegative number.")


def build(config):
    validate_config(config)
    market = config["market"]
    observation_label, entity_label, mechanism = MARKETS[market]
    observation_id, entity_id = market + ":demo-observation", market + ":demo-entity"
    # Fixed synthetic values: never use these as financial observations.
    previous, current = 100, 112
    change_pct = round((current - previous) / previous * 100, 6)
    graph = {
        "schema_version": "0.1.0", "mode": "demo", "market": market,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "research_question": config["research_question"],
        "disclaimer": "Fictional fixtures only. Not live data, verified causality, investment advice or a predictive signal.",
        "cadence": {"requested": config["cadence"], "active": False, "note": "Run once. Configure your own scheduler separately."},
        "nodes": [
            {"id": observation_id, "type": "observation", "label": observation_label,
             "observations": [{"metric": "example_index", "previous": previous, "value": current, "unit": "index_points", "change_pct": change_pct,
                               "observed_at": "2026-01-02T00:00:00Z", "source_id": "fixture-001", "verification": "synthetic"}]},
            {"id": entity_id, "type": "research_subject", "label": entity_label, "observations": []}
        ],
        "edges": [{"id": market + ":demo-edge", "from": observation_id, "to": entity_id, "relation": "may_affect",
                   "mechanism": mechanism, "status": "hypothesis", "evidence_ids": ["fixture-001"]}],
        "sources": [{"id": "fixture-001", "kind": "synthetic", "reference": "starter/run.py: fixed example index 100 to 112", "note": "Authored demonstration, not external evidence."}]
    }
    queue = {
        "schema_version": "0.1.0", "mode": "demo", "market": market, "items": [],
        "note": "A snapshot review queue, not a notification delivery service. Re-running recreates the same fixture items; no emails, trades or webhooks are sent."
    }
    if change_pct >= config["review_rule"]["threshold"]:
        queue["items"].append({"id": market + ":fixture-001:review", "kind": "review_required", "subject_id": entity_id,
                               "reason": "Synthetic index rose 12%; it meets your configured review threshold.",
                               "rule": config["review_rule"], "evidence_ids": ["fixture-001"],
                               "graph_path": [observation_id, entity_id], "relationship_status": "hypothesis"})
    return graph, queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.example.json"))
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing outputs are never overwritten.")
    args = parser.parse_args()
    try:
        graph, queue = build(json.loads(args.config.read_text(encoding="utf-8")))
        args.output.mkdir(parents=True, exist_ok=False)
        for name, value in (("graph.json", graph), ("review-queue.json", queue)):
            with (args.output / name).open("x", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, allow_nan=False)
                handle.write("\n")
    except (OSError, ValueError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1
    print(f"DEMO ONLY: wrote graph.json and review-queue.json to {args.output}")
    print("All data is fictional. No network calls, schedule, notifications or trades.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
