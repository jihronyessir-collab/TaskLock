"""Regression tests for GitHub API 404 and safe TaskLock update fallback."""
import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from tasklock_updates import ReleaseLookupError, latest_published_release


REPO = "jihronyessir-collab/TaskLock"


def release(version, *, tag=None, installer=True, digest=""):
    tag = tag or f"v{version}-beta.1"
    name = f"TaskLock-v{version}-Setup.exe"
    return {
        "tag_name": tag,
        "draft": False,
        "prerelease": "-beta" in tag,
        "assets": [{
            "name": name,
            "browser_download_url": f"https://github.com/{REPO}/releases/download/{tag}/{name}",
            "size": 14000000,
            "digest": digest,
        }] if installer else [],
    }


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def fake_opener(api, pages):
    def open_request(request, timeout=8):
        url = request.full_url
        if "api.github.com" in url:
            payload = api
        elif "github.io" in url:
            payload = pages
        else:
            raise AssertionError("Unexpected update source: " + url)
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(json.dumps(payload).encode("utf-8"))
    return open_request


def test_api_works_and_prefers_latest_version():
    version, result = latest_published_release(
        REPO, opener=fake_opener(
            [release("5.0.0"), release("5.1.1"), release("5.1.0")], []))
    assert version == (5, 1, 1)
    assert result["tag_name"] == "v5.1.1-beta.1"


def test_http_404_uses_github_pages_fallback():
    error = HTTPError("https://api.github.com/", 404, "Not Found", None, None)
    version, result = latest_published_release(
        REPO, opener=fake_opener(error, {"releases": [release("5.1.1")]}))
    assert version == (5, 1, 1)
    assert result["assets"][0]["name"] == "TaskLock-v5.1.1-Setup.exe"


def test_api_network_error_uses_pages():
    version, _ = latest_published_release(
        REPO, opener=fake_opener(URLError("blocked"), [release("5.1.0")]))
    assert version == (5, 1, 0)


def test_both_sources_unavailable_has_helpful_error():
    with pytest.raises(ReleaseLookupError, match="Release downloads"):
        latest_published_release(
            REPO, opener=fake_opener(URLError("blocked"), URLError("blocked")))


def test_does_not_accept_foreign_release_download_url():
    spoof = release("99.0.0")
    spoof["assets"][0]["browser_download_url"] = "https://attacker.example/malware.exe"
    version, _ = latest_published_release(
        REPO, opener=fake_opener([spoof, release("5.1.0")], []))
    assert version == (5, 1, 0)


def test_does_not_accept_wrong_version_asset():
    spoof = release("9.0.0")
    spoof["assets"][0]["name"] = "TaskLock-v5.1.0-Setup.exe"
    version, _ = latest_published_release(
        REPO, opener=fake_opener([spoof, release("5.1.0")], []))
    assert version == (5, 1, 0)


def test_stable_release_outranks_beta_of_same_version():
    version, result = latest_published_release(
        REPO, opener=fake_opener(
            [release("5.1.1", tag="v5.1.1-beta.1"),
             release("5.1.1", tag="v5.1.1")], []))
    assert version == (5, 1, 1)
    assert result["tag_name"] == "v5.1.1"


def test_reject_invalid_repo():
    with pytest.raises(ReleaseLookupError, match="invalid"):
        latest_published_release("../wrong")
