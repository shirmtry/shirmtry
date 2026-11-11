#!/usr/bin/env python3
"""Rewrite the README telemetry block between AUTO markers."""

import json
import os
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LOGIN = os.environ.get("GH_LOGIN", "shirmtry")
TOKEN = os.environ.get("GH_TOKEN", "")
README = Path("README.md")
START = "<!-- AUTO:START -->"
END = "<!-- AUTO:END -->"


def api(path: str):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{LOGIN}-profile-telemetry",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> None:
    user = api(f"/users/{LOGIN}")
    repos = api(f"/users/{LOGIN}/repos?per_page=100&type=owner")

    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)
    languages = Counter(
        r["language"] for r in owned if r.get("language")
    )
    top_language = ", ".join(lang for lang, _ in languages.most_common(3)) or "n/a"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    block = (
        f"{START}\n"
        f"<sub>Last auto-update: <b>{stamp}</b> · "
        f"<b>{user.get('public_repos', len(owned))}</b> public repos · "
        f"<b>{stars}</b> stars · top language <b>{top_language}</b> · "
        f'<a href=".github/workflows/update-profile.yml">telemetry workflow</a></sub>\n'
        f"{END}"
    )

    text = README.read_text(encoding="utf-8")
    updated, count = re.subn(
        rf"{re.escape(START)}.*?{re.escape(END)}", block, text, flags=re.S
    )
    if count != 1:
        raise SystemExit(f"expected exactly one AUTO block, found {count}")

    if updated != text:
        README.write_text(updated, encoding="utf-8", newline="\n")
        print(f"updated: {stamp}, {len(owned)} repos, {stars} stars, {top_language}")
    else:
        print("no change")


if __name__ == "__main__":
    main()
