# Wolfveil security design — draft

**Do not market this prototype as secure, audited, or ready for end users.**

## Threat model

A VPN can encrypt network traffic from the device to a chosen VPN endpoint.
It does not make websites trustworthy, prevent phishing, remove malware, or
protect the endpoint itself. VPN operators may still see connection metadata.
Ad/tracker blocking based on DNS cannot block every advertisement.

## First-phase safeguards

- Use the official WireGuard client and protocol; never invent encryption.
- No silent tunnel connection or system DNS changes.
- Require explicit user action for tunnel installation and removal.
- Never print, upload, log, or commit WireGuard private keys or .conf files.
- Validate file names, basic configuration structure, and IP networks.
- Execute WireGuard via subprocess argument arrays (never through a shell).
- Never run unknown executables downloaded from the internet.
- No browsing-history collection or telemetry in the prototype.
- Report errors without echoing the secret contents of configuration files.

## Before a public release

- Add a proper Windows GUI with accessible consent and status indicators.
- Audit file permissions and secure handling of sensitive config files.
- Verify IPv4/IPv6 routing, DNS behavior, tunnel failures, and kill-switch
  behavior under realistic Windows conditions.
- Choose, disclose, and test an actual VPN server/provider and privacy policy.
- Add independent security review, reproducible builds, and signed installers.

**Never claim a kill switch or active ad blocking until implemented and tested.**
