"""Publish a small, verified GitHub Pages release feed for TaskLock.

This runs in the official GitHub Pages deployment workflow. It only copies
public GitHub Release metadata and never fabricates a download URL.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-beta\.\d+)?$")
FILE = re.compile(r"^TaskLock-v(\d+)\.(\d+)\.(\d+)-(Setup\.exe|Windows\.zip)$", re.I)


def build_feed(releases: list, repo: str) -> dict:
    output = []
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name", "")
        match = TAG.fullmatch(tag) if isinstance(tag, str) else None
        if not match:
            continue
        version = tuple(int(x) for x in match.groups()[:3])
        assets = []
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            match_file = FILE.fullmatch(name) if isinstance(name, str) else None
            if not match_file or tuple(int(x) for x in match_file.groups()[:3]) != version:
                continue
            expected_url = f"https://github.com/{repo}/releases/download/{tag}/{name}"
            if asset.get("browser_download_url") != expected_url:
                continue
            size = asset.get("size", 0)
            if not isinstance(size, int) or size <= 0:
                continue
            assets.append({
                "name": name,
                "browser_download_url": expected_url,
                "size": size,
                "digest": asset.get("digest") or "",
            })
        if assets:
            output.append({
                "tag_name": tag,
                "prerelease": bool(release.get("prerelease")),
                "draft": False,
                "assets": assets,
            })
    if not output:
        raise RuntimeError("No valid public TaskLock releases; refusing to publish an empty feed.")
    return {"product": "TaskLock", "repository": repo, "releases": output}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "TaskLock-Pages-Release-Feed",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"https://api.github.com/repos/{args.repo}/releases?per_page=20",
        headers=headers,
    )
    with urlopen(request, timeout=20) as response:
        releases = json.load(response)
    feed = build_feed(releases, args.repo)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")
    print(f"Published metadata for {len(feed['releases'])} verified public releases.")


if __name__ == "__main__":
    main()
