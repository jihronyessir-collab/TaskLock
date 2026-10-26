# Wolfveil — Tavlokyn Studios VPN project

**Status: early development / prototype. Not a public VPN service.**

Wolfveil is a planned Windows privacy app. This repository folder is a temporary
development workspace until Wolfveil has its own dedicated repository.

## What this first prototype actually does

- Validates a user-supplied WireGuard tunnel configuration without displaying or logging keys.
- Uses the **official WireGuard for Windows** client to install, query, or remove a
  tunnel service **only when the user explicitly requests it**.
- Provides an offline **ad-blocklist preview** to see whether a domain matches a
  local list. **This does not yet block live DNS requests.**
- Includes automated tests and a security-first roadmap.

This prototype **does not** supply VPN servers, VPN accounts, subscriptions,
network routing infrastructure, active DNS blocking, antivirus, or a firewall.
A VPN protects traffic between a device and the chosen VPN server; it does not
make the device immune to malware or unauthorized access.

## Prerequisites

- Windows 10/11, Python 3.10+.
- [WireGuard for Windows](https://www.wireguard.com/install/) installed separately.
- A valid WireGuard client configuration from a VPN server you own or trust.
- Administrator approval may be required by Windows to manage tunnel services.

**Never share your WireGuard configuration or private key publicly.**
Never run an untrusted tunnel configuration.

## Developer commands

Run from this folder:

\`\`\`powershell
python -m wolfveil check "C:\path\mytunnel.conf"
python -m wolfveil status mytunnel
python -m wolfveil connect "C:\path\mytunnel.conf" --confirm
python -m wolfveil disconnect mytunnel --confirm
python -m wolfveil adblock-check ads.example --blocklist sample-blocklist.txt
\`\`\`

Connect/disconnect are opt-in and make system changes via the official WireGuard
client. You can also use WireGuard's own UI instead.

## Next milestones

1. Dedicated Wolfveil repository, app branding, and a simple Windows UI.
2. Tunnel configuration import with secure storage and user consent.
3. Optional, auditable DNS ad/tracker blocking **inside the VPN tunnel**, with
   explicit provider choice and DNS leak testing.
4. Connection verification, clear privacy disclosures, security review, and
   Windows packaging.
5. Only after independent testing: a public beta.

See [SECURITY.md](SECURITY.md) for the initial threat model.
