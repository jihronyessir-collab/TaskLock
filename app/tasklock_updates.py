"""Safe TaskLock update discovery with a GitHub Pages fallback.

GitHub Releases API is the primary source. The fallback is a release feed
published on the official TaskLock GitHub Pages site by GitHub Actions.
Only verified-looking release assets from the configured repository are used.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_INSTALLER = re.compile(r"^TaskLock-v(\d+)\.(\d+)\.(\d+)-(Setup\.exe|Windows\.zip)$", re.I)
_MAX_BYTES = 250 * 1024 * 1024


class ReleaseLookupError(RuntimeError):
    """Neither official release source provided a usable release."""


def _validated_release(release: object, repo: str) -> tuple[tuple[int, ...], dict] | None:
    if not isinstance(release, dict) or release.get("draft"):
        return None
    tag = release.get("tag_name", "")
    match = _TAG.fullmatch(tag) if isinstance(tag, str) else None
    if not match:
        return None
    version = tuple(int(n) for n in match.group(1, 2, 3))
    beta_number = int(match.group(4)) if match.group(4) else None
    # A stable release outranks its beta; a newer version outranks any older version.
    sort_key = (*version, 1 if beta_number is None else 0, beta_number or 0)
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        return None
    good_assets = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name", "")
        filename = _INSTALLER.fullmatch(name) if isinstance(name, str) else None
        if not filename or tuple(int(x) for x in filename.group(1, 2, 3)) != version:
            continue
        expected_url = f"https://github.com/{repo}/releases/download/{tag}/{name}"
        if asset.get("browser_download_url") != expected_url:
            continue
        size = asset.get("size", 0)
        if not isinstance(size, int) or not 0 < size <= _MAX_BYTES:
            continue
        digest = asset.get("digest", "")
        if digest and (not isinstance(digest, str)
                       or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest)):
            continue
        good_assets.append({
            "name": name, "browser_download_url": expected_url,
            "size": size, "digest": digest,
        })
    if not good_assets:
        return None
    return sort_key, {
        "tag_name": tag, "prerelease": beta_number is not None,
        "draft": False, "assets": good_assets,
    }


def _fetch_json(url: str, *, opener, timeout: int) -> object:
    request = Request(url, headers={
        "User-Agent": "TaskLock-UpdateChecker/1.0",
        "Accept": "application/vnd.github+json" if "api.github.com" in url else "application/json",
        "Cache-Control": "no-cache",
    })
    with opener(request, timeout=timeout) as response:
        return json.load(response)


def latest_published_release(repo: str, *, opener=None, timeout: int = 8) -> tuple[tuple[int, int, int], dict]:
    """Return (semantic version, safe release) from API or official Pages feed.

    Does not download or install any software. The feed is a fallback when the
    GitHub API returns HTTP 404, is blocked, or otherwise cannot be reached.
    """
    if not isinstance(repo, str) or not _REPO.fullmatch(repo):
        raise ReleaseLookupError("The configured GitHub repository is invalid.")
    if opener is None:
        opener = urlopen
    owner, project = repo.split("/", 1)
    sources = (
        f"https://api.github.com/repos/{repo}/releases?per_page=20",
        f"https://{owner}.github.io/{project}/release-info.json",
    )
    for source in sources:
        try:
            payload = _fetch_json(source, opener=opener, timeout=timeout)
            releases = payload.get("releases") if isinstance(payload, dict) else payload
            if not isinstance(releases, list):
                continue
            options = [r for r in (_validated_release(item, repo) for item in releases) if r]
            if options:
                sort_key, release = max(options, key=lambda pair: pair[0])
                return sort_key[:3], release
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError):
            continue
    raise ReleaseLookupError(
        "The GitHub API and the official TaskLock website couldn't confirm a release. "
        "You can open Release downloads to check manually."
    )
