# Tavlokyn Studios — Phase Four OVERDRIVE

Phase Four is an **alpha development phase**. Phase Five is reserved for release-candidate testing and final public launch. No unfinished prototype should be described as feature-complete.

## TaskLock V7.0.0-alpha.1
- New Python/Tkinter desktop interface: command center, task board, focus lab, analytics and local SQLite data.
- JSON import/export; four automated core tests and GUI smoke test under a virtual display passed.
- Source ZIP: https://media.base44.com/files/public/6aded06e3023dd51b6c7103c/ab3f41f17_TaskLock-V7-Alpha1-Source.zip
- Windows GitHub Actions workflow builds an alpha EXE and publishes a **prerelease only if tests and packaging pass**. No successful Windows build has been independently verified yet.
- Gaps: feature parity with V6, browser-blocking integration, reminders, Windows installer, migration and accessibility QA.

## Waventra V4 Plugin Lab Alpha
- Online studio: https://waventra-studio-web-5e2bc7eb.base44.app/studio.html
- Built-in EQ, drive, tremolo, delay, reverb, compressor; live playback and WAV export routing.
- Gaps: real-browser audio tests, automation, external plugin API/VST support, multitrack audio mixing, account sync.

## FluxFrame V3 Alpha
- Online editor: https://obedient-focus-lock-flow.base44.app/fluxframe/studio
- Draggable playhead, Ctrl+B split, segment trims, motion presets, frame caching and experimental silent WebM export.
- Gaps: MP4 encoding, soundtrack mixing, true multi-track editing, accurate waveform and keyframes, large-file stress tests.

## OrbitDesk V2.1
- Online wallpaper lab: https://obedient-focus-lock-flow.base44.app/orbitdesk
- Six CSS animation overlays and glow/speed controls; desktop native version remains future work.
- Gaps: Windows wallpaper engine, multi-monitor support, efficient native animation and wallpaper persistence.

## Lumen V0.3
- Free GitHub Pages lab: https://jihronyessir-collab.github.io/TaskLock/lumen/
- Rule-based conversation and teachable local notebook without Base44 credits.
- **Important:** GitHub Pages hosts static HTML; it does not supply an AI model or reasoning. A real conversational model will require on-device inference or an approved backend. The earlier Base44 hosted model is experimental and may be unavailable without credits.

## Phase Five release gates
1. Verify Windows builds and installers on actual Windows hardware.
2. Reproduce and close critical playback/audio/data-loss bugs.
3. Add tests for import/export, large projects, offline behavior and accessibility.
4. Security and privacy review, especially authentication and user-supplied files.
5. Clear release notes, support links, backups, versioning and rollback paths.
