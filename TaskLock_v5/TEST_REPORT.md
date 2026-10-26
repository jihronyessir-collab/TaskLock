# TaskLock v5 — Build and Test Report

**Test environment:** Linux Python 3.13, Tk/Tcl in Xvfb virtual display, Node.js 22.  
**Release candidate:** `5.0.0` (not yet compiled or tested as a Windows 11 EXE).

### Passed locally

- `python -m py_compile app/*.py` — Python compilation
- `python -m pytest tests -q` — **11 tests passed**, including migration, backup/restore, recurrence, subtasks and pause behavior
- `node tests/browser_extension_test.js` — domain/subdomain block and pause decisions passed using Chrome API mocks
- `xvfb-run -a python tests/gui_smoke.py` — all seven screens opened, theme switching, calendar day/week/month, task creation, local HTTP focus bridge, timer, full-screen reminder, Esc/emergency exit, and screenshot capture
- New PNG/ICO icon generated; images included in the release candidate

### Not yet tested or published

- Windows 11 device execution, taskbar behavior, sleep/wake recovery, actual Windows audio hardware, Windows installer build/install/uninstall
- Real Chrome and Edge installed extensions and browsing sessions (only mock logic + local HTTP bridge tested)
- Smart App Control signature/reputation trust and Windows code-signing
- Remote GitHub Actions Windows build and deployment (requires a real repo and publishing access)
- Live website, Base44 changes, and downloadable public release links

**Conclusion:** Source-code release candidate is suitable for private testing, **not yet production-validated**. Do not advertise it as a tested or signed Windows installer until those tests are completed.
