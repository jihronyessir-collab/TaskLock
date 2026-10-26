"""Explicit, user-initiated integration with official WireGuard for Windows."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .config import ConfigError, TunnelInfo, validate_config_file, validate_tunnel_name


class WireGuardUnavailable(RuntimeError):
    pass


def wireguard_executable() -> Path:
    if os.name != "nt":
        raise WireGuardUnavailable("Connecting is supported on Windows only.")
    program_files = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "WireGuard" / "wireguard.exe",
        Path(os.environ.get("ProgramW6432", r"C:\Program Files")) / "WireGuard" / "wireguard.exe",
    ]
    for path in program_files:
        if path.is_file():
            return path
    candidate = shutil.which("wireguard.exe")
    if candidate:
        return Path(candidate)
    raise WireGuardUnavailable("Install official WireGuard for Windows first.")


def _run(args: list[str]) -> str:
    """Do not include config text or command output in raised exceptions."""
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True,
                                timeout=40, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        raise WireGuardUnavailable("WireGuard command could not finish.") from None
    if result.returncode != 0:
        raise WireGuardUnavailable(
            "WireGuard could not complete the request. Check installation, "
            "administrator permissions, and the tunnel name."
        )
    return result.stdout.strip()


def connect(config_path: str | Path, *, confirmed: bool = False) -> TunnelInfo:
    if not confirmed:
        raise PermissionError("Explicit confirmation is required to connect.")
    info = validate_config_file(config_path)
    exe = wireguard_executable()
    # Official WireGuard for Windows installs a tunnel service for the config.
    _run([str(exe), "/installtunnelservice", str(Path(config_path).expanduser().resolve())])
    return info


def disconnect(tunnel_name: str, *, confirmed: bool = False) -> None:
    if not confirmed:
        raise PermissionError("Explicit confirmation is required to disconnect.")
    name = validate_tunnel_name(tunnel_name)
    exe = wireguard_executable()
    _run([str(exe), "/uninstalltunnelservice", name])


def status(tunnel_name: str) -> str:
    name = validate_tunnel_name(tunnel_name)
    if os.name != "nt":
        return "Windows only"
    try:
        result = subprocess.run(["sc.exe", "query", "WireGuardTunnel$" + name],
                                capture_output=True, text=True, check=False,
                                timeout=10, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        return "Unknown"
    if result.returncode != 0:
        return "Not installed"
    if "RUNNING" in result.stdout:
        return "Running (tunnel service)"
    if "STOPPED" in result.stdout:
        return "Stopped"
    return "Unknown"
