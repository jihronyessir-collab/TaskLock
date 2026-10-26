"""Read-only validation for user-supplied WireGuard tunnel configurations.

Never include configuration text or key material in error messages.
"""
from __future__ import annotations

import base64
import ipaddress
import re
from dataclasses import dataclass
from pathlib import Path

_NAME = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_ENDPOINT = re.compile(r"^(?:\[[0-9a-fA-F:.%]+\]|[^:\s]+):([0-9]{1,5})$")
_MAX_CONFIG_BYTES = 64 * 1024


class ConfigError(ValueError):
    """Configuration is missing required fields or contains invalid values."""


@dataclass(frozen=True)
class TunnelInfo:
    name: str
    peers: int
    addresses: tuple[str, ...]
    has_dns: bool


def validate_tunnel_name(name: str) -> str:
    if not _NAME.fullmatch(name):
        raise ConfigError("Tunnel name must be 1-32 letters, numbers, _ or -.")
    return name


def _valid_key(value: str) -> bool:
    try:
        return len(base64.b64decode(value, validate=True)) == 32
    except (ValueError, base64.binascii.Error):
        return False


def validate_config_text(text: str, name: str) -> TunnelInfo:
    validate_tunnel_name(name)
    section: str | None = None
    interface: dict[str, str] = {}
    peers: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.lower() == "[interface]":
            if interface or section == "interface":
                raise ConfigError("Only one [Interface] section is supported.")
            section = "interface"
            continue
        if line.lower() == "[peer]":
            peers.append({})
            section = "peer"
            continue
        if line.startswith("["):
            raise ConfigError("Unknown configuration section.")
        if section is None or "=" not in line:
            raise ConfigError("Invalid WireGuard configuration structure.")
        key, value = (part.strip() for part in line.split("=", 1))
        if not key or not value:
            raise ConfigError("A WireGuard configuration field is empty.")
        target = interface if section == "interface" else peers[-1]
        if key.lower() in target:
            raise ConfigError("Duplicate WireGuard configuration field.")
        target[key.lower()] = value

    if not _valid_key(interface.get("privatekey", "")):
        raise ConfigError("[Interface] must have a valid PrivateKey.")
    addresses = tuple(x.strip() for x in interface.get("address", "").split(",") if x.strip())
    if not addresses:
        raise ConfigError("[Interface] needs an Address.")
    try:
        for address in addresses:
            ipaddress.ip_interface(address)
    except ValueError as exc:
        raise ConfigError("Invalid interface IP address.") from None

    if not peers:
        raise ConfigError("At least one [Peer] is required.")
    for peer in peers:
        if not _valid_key(peer.get("publickey", "")):
            raise ConfigError("[Peer] must have a valid PublicKey.")
        endpoint = _ENDPOINT.fullmatch(peer.get("endpoint", ""))
        if not endpoint or not 1 <= int(endpoint.group(1)) <= 65535:
            raise ConfigError("[Peer] needs a valid host:port Endpoint.")
        networks = [x.strip() for x in peer.get("allowedips", "").split(",") if x.strip()]
        if not networks:
            raise ConfigError("[Peer] needs AllowedIPs.")
        try:
            for network in networks:
                ipaddress.ip_network(network, strict=False)
        except ValueError:
            raise ConfigError("Invalid AllowedIPs network.") from None

    return TunnelInfo(name=name, peers=len(peers), addresses=addresses,
                      has_dns=bool(interface.get("dns")))


def validate_config_file(path: str | Path) -> TunnelInfo:
    file = Path(path).expanduser().resolve()
    if file.suffix.lower() != ".conf":
        raise ConfigError("Select a WireGuard .conf file.")
    validate_tunnel_name(file.stem)
    if not file.is_file():
        raise ConfigError("WireGuard configuration file not found.")
    if file.stat().st_size > _MAX_CONFIG_BYTES:
        raise ConfigError("Configuration file is too large.")
    try:
        text = file.read_text(encoding="utf-8-sig")
    except (UnicodeError, OSError):
        raise ConfigError("Unable to read configuration file.") from None
    return validate_config_text(text, file.stem)
