"""Wolfveil prototype tests run as part of the Windows CI build."""
import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "projects" / "wolfveil"))
from wolfveil.config import ConfigError, validate_config_text, validate_tunnel_name
from wolfveil.dns_filter import Blocklist
from wolfveil.manager import connect, disconnect


KEY = base64.b64encode(bytes(range(32))).decode()
VALID = f"""
[Interface]
PrivateKey = {KEY}
Address = 10.9.0.2/32
DNS = 10.9.0.1

[Peer]
PublicKey = {KEY}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = vpn.example:51820
"""


def test_valid_config():
    result = validate_config_text(VALID, "wolfveil_test")
    assert result.name == "wolfveil_test"
    assert result.peers == 1
    assert result.has_dns
    assert result.addresses == ("10.9.0.2/32",)


def test_secret_is_never_in_error():
    broken = VALID.replace("Endpoint = vpn.example:51820", "Endpoint = invalid")
    with pytest.raises(ConfigError) as error:
        validate_config_text(broken, "wolfveil_test")
    assert KEY not in str(error.value)


def test_reject_bad_names():
    for name in ("../../other", "hello world", "a" * 33, "test;whoami"):
        with pytest.raises(ConfigError):
            validate_tunnel_name(name)


def test_blocklist_exact_and_subdomain():
    blocklist = Blocklist.from_text(
        "0.0.0.0 ads.example\n||analytics.example^\n127.0.0.1 tracking.example")
    assert blocklist.is_blocked("ads.example")
    assert blocklist.is_blocked("pixel.ads.example")
    assert blocklist.is_blocked("tracking.example")
    assert not blocklist.is_blocked("notads.example")
    assert not blocklist.is_blocked("ads.example.evil")


def test_connection_requires_consent():
    with pytest.raises(PermissionError):
        connect("not-real.conf")
    with pytest.raises(PermissionError):
        disconnect("wolfveil_test")
