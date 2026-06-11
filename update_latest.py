#!/usr/bin/env python3
"""Fetch the latest toroIQ Substack post and update latest.json on toroiq.com.

Runs on the Mac via launchd (com.nimitmehra.toroiq-latest) because Substack's
bot protection blocks GitHub Actions runner IPs (403). Stdlib only — no venv.
"""
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent
FEED = "https://toroiq.substack.com/feed"


def main() -> int:
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    item = root.find(".//item")
    data = {
        "title": (item.findtext("title") or "").strip(),
        "link": (item.findtext("link") or "").strip(),
        "date": (item.findtext("pubDate") or "").strip(),
    }
    if not (data["title"] and data["link"]):
        print("empty feed item — keeping existing latest.json", file=sys.stderr)
        return 1

    out = REPO / "latest.json"
    old = json.loads(out.read_text()) if out.exists() else {}
    if old == data:
        print("latest.json already current:", data["title"])
        return 0

    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    for cmd in (
        ["git", "-C", str(REPO), "pull", "--rebase", "--quiet"],
        ["git", "-C", str(REPO), "add", "latest.json"],
        ["git", "-C", str(REPO), "commit", "-m", "latest.json: auto-update from Substack feed", "--quiet"],
        ["git", "-C", str(REPO), "push", "--quiet"],
    ):
        subprocess.run(cmd, check=True)
    print("updated + pushed:", data["title"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
