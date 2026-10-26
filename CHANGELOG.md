# TaskLock — Changelog

## v5.1.1 — Update Check Reliability (Windows public beta)
- Fixed Check for Updates reporting HTTP Error 404 by adding a fallback to the official GitHub Pages release feed.
- Verified installer filenames, versions, URLs, and sizes before offering downloads.
- Improved messages when neither update source is available.
- Kept all V5.1.0 Color & Sound features and local task data unchanged.
- Added regression tests for API 404, network failures, and unsafe release download links.


## v5.1.0 — Color & Sound Edition (Windows public beta)
- Added five expressive color palettes: Inferno Red, Phantom Violet, Emerald Pulse, Solar Flare, and Arctic Frost; retained all existing themes.
- Made the sidebar and updates panel better reflect the selected palette.
- Added eight original synthesized, instrument-inspired alert melodies: Brass Fanfare, Trombone Groove, Drumline Call, Synthwave Lift, String Serenade, Piano Cascade, Marimba Steps, and Electric Guitar Hook.
- Retained existing 12 alerts, per-category choices, custom WAV, silence, and volume controls.
- Improved update checking to recognize published GitHub beta releases.
- Preserved task data and local settings on upgrades. Beta testing continues.


## v5.0.0 — BLUECORE (source release candidate, October 2026)
- Replaced feather identity with a custom futuristic electric-blue lock emblem (PNG, ICO).
- Refreshed the blue-black command-center dashboard, brand navigation, task summary cards and daily progress.
- Added task subtasks with persistent completion checkboxes, advanced recurrence (weekdays, every two weeks, every three months, yearly), and task categories/priorities.
- Added month, week and day calendar views.
- Added a first-run welcome experience.
- Upgraded full-screen task reminders with configurable snooze and safe emergency exit.
- Preserved and refreshed online-homework Focus Mode, added a focus timer and safe pause controls.
- Expanded ringtone collection to 12 original generated PCM WAV sounds, per-category sound choices and a volume slider.
- Added themes, accessibility font sizing and a motion preference.
- Added automatic pre-v5 data snapshot, exportable local backup ZIP and restore functionality.
- Added Windows setup definition, Windows GitHub Actions build and release metadata generator.
- Updated static download website to display real Windows releases only after publication.

**Not yet verified:** actual Windows 11 behavior, audio playback on Windows, real Chrome/Edge integration, Windows installer compilation, Smart App Control trust, public release hosting and real Base44 product links.

## v4.0.0 — Blue & Black redesign
- Dashboard, task management, calendar, homework focus section, eight ringtones and update-log infrastructure.

## v3.0.0 — Homework Focus Mode
- Optional Chrome/Edge website blocking for active homework tasks.

## v2.0.0 — Ringtone Edition
- Three generated reminder tones and custom WAV support.

## v1.0.0 — First release
- Local task storage, basic calendar, recurring alerts, full-screen Done/Snooze/Emergency Exit.
