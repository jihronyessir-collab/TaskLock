"""Wolfveil prototype command line. No connections without --confirm."""
from __future__ import annotations

import argparse
from pathlib import Path

from .config import ConfigError, validate_config_file
from .dns_filter import Blocklist
from .manager import WireGuardUnavailable, connect, disconnect, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wolfveil", description="Wolfveil early-development WireGuard client")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Validate a local WireGuard .conf")
    check.add_argument("config")
    up = commands.add_parser("connect", help="Install a WireGuard tunnel service")
    up.add_argument("config")
    up.add_argument("--confirm", action="store_true", required=True,
                    help="Explicitly authorize tunnel installation")
    down = commands.add_parser("disconnect", help="Remove a WireGuard tunnel service")
    down.add_argument("name")
    down.add_argument("--confirm", action="store_true", required=True,
                      help="Explicitly authorize tunnel removal")
    stat = commands.add_parser("status", help="Check the Windows tunnel service")
    stat.add_argument("name")
    block = commands.add_parser("adblock-check", help="Preview a local domain blocklist")
    block.add_argument("domain")
    block.add_argument("--blocklist", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            info = validate_config_file(args.config)
            print(f"Valid configuration: {info.name}; peers: {info.peers}; "
                  f"DNS configured: {'yes' if info.has_dns else 'no'}")
        elif args.command == "connect":
            info = connect(args.config, confirmed=True)
            print(f"Requested WireGuard tunnel: {info.name}. "
                  "Verify the connection and DNS independently.")
        elif args.command == "disconnect":
            disconnect(args.name, confirmed=True)
            print(f"Removed WireGuard tunnel service: {args.name}")
        elif args.command == "status":
            print(status(args.name))
        elif args.command == "adblock-check":
            blocklist = Blocklist.from_text(args.blocklist.read_text(encoding="utf-8"))
            print("Would block" if blocklist.is_blocked(args.domain) else "No match")
            print("Preview only: live DNS blocking is NOT implemented.")
    except (ConfigError, WireGuardUnavailable, ValueError, OSError) as exc:
        print(f"Wolfveil: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
