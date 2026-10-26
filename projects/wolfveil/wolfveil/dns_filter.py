"""Offline ad/tracker blocklist preview, NOT an active DNS resolver."""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

_DOMAIN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_domain(domain: str) -> str:
    name = domain.strip().lower().rstrip(".")
    if not _DOMAIN.fullmatch(name) or len(name) > 253:
        raise ValueError("Enter a valid domain name.")
    return name


@dataclass(frozen=True)
class Blocklist:
    domains: frozenset[str]

    @classmethod
    def from_text(cls, text: str) -> "Blocklist":
        entries: set[str] = set()
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "!", "@@")):
                continue
            if line.startswith("||") and line.endswith("^"):
                candidate = line[2:-1]
            else:
                parts = line.split()
                if len(parts) == 2:
                    try:
                        ip = ipaddress.ip_address(parts[0])
                    except ValueError:
                        continue
                    if not ip.is_loopback and not ip.is_unspecified:
                        continue
                    candidate = parts[1]
                elif len(parts) == 1:
                    candidate = parts[0]
                else:
                    continue
            try:
                entries.add(normalize_domain(candidate))
            except ValueError:
                continue
        return cls(frozenset(entries))

    def is_blocked(self, domain: str) -> bool:
        name = normalize_domain(domain)
        return any(name == blocked or name.endswith("." + blocked)
                   for blocked in self.domains)
