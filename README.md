# TaskLock v5.0.0 — BLUECORE

**Publisher brand:** Tavlokyn Studios  
**Product slogan:** Stay Focused. Finish Strong.  
**Status:** Source release candidate — Windows installer is prepared for compilation, not yet built or published.  
**Price:** Free. **Data:** Stored locally on your computer.

## What is inside

| Feature | Implemented in this source | Limitations |
| --- | --- | --- |
| Brand-new blue lock emblem | PNG, multi-size ICO, 512 PNG | Not trademark-cleared |
| Futuristic Windows dashboard | New BLUECORE UI, progress, overview, sidebar | Tkinter rather than a GPU-animated UI |
| Tasks | Search/filter/edit, notes, priority/category, subtasks | Date/time typed as YYYY-MM-DD + 24h clock |
| Recurrence | Daily, weekdays, weekly, 2 weeks, monthly, 3 months, yearly | Follows local clock, app must be running |
| Calendar | Day, week, month views | No drag/drop calendar editing |
| First-run welcome | Intro dialog + safety controls | Existing users may see it once after upgrade |
| Alerts | Full-screen Done, Snooze, Start Homework, Emergency Exit/Esc | Windows must be awake and TaskLock running |
| Focus | 25-minute configurable timer; pausable blocker with Chrome/Edge extension | Does not block every browser or verify completion |
| Sounds | 12 generated WAV melodies, custom PCM WAV, category sounds, volume | Audio playback on Windows not yet tested on hardware |
| Preferences | 4 palettes, text size, reduced-motion preference, timer settings | Some accent panels retain the BLUECORE color |
| Storage | Auto pre-v5 copy, backup ZIP and restore | No sync or cloud account |
| Updates | In-app changelog, GitHub release checker and download prompt | Active only after a real public release repository is configured |
| Windows distribution | PyInstaller portable EXE builder + Inno Setup installer + GitHub Actions | Windows installer must still run on Windows |
| TaskLock website | Static free website with a download button linked to actual published releases | Not publicly deployed yet |

## Try the app on Windows 11 with Python already installed

1. Extract the `TaskLock_v5_Source_and_Website.zip` archive.
2. Open `TaskLock_v5` and double-click `Run_From_Source.bat` (Python 3.10+ with Tkinter required).
3. If you used TaskLock v4, v5 reads `%APPDATA%\TaskLock\tasks.json` and makes a snapshot in `%APPDATA%\TaskLock\pre_v5_backup` before loading existing data.
4. In **Tasks**, add your assignment and optional subtasks. In **Focus**, start a session.
5. In **Settings**, export a ZIP backup before experimenting further.

### Build the Windows EXE and installer locally

1. Double-click `Build_Windows.bat` (requires Python and internet to install the free PyInstaller build tool).
2. It creates `dist\TaskLock.exe` and `release\TaskLock-v5.0.0-Windows.zip`.
3. For the **actual Windows installer**, also install free [Inno Setup 6](https://jrsoftware.org/isinfo.php), then rerun the build script.
4. When successful, `release\TaskLock-v5.0.0-Setup.exe` appears. This installer creates Start Menu shortcuts and an optional desktop shortcut. It installs per-user and does **not** erase `%APPDATA%\TaskLock` on uninstall.

**Security note:** Unsigned software may be blocked by Windows Smart App Control. Do not turn off Smart App Control just to use TaskLock. Instead, have the release built, tested, and eventually code-signed by the publisher.

### Enable Chrome / Edge website blocking

1. Keep TaskLock open.
2. Chrome: visit `chrome://extensions`; Edge: `edge://extensions`.
3. Enable Developer mode; choose **Load unpacked**, then choose `Browser_Extension` from the extracted source, portable ZIP, or installed program folder.
4. Add a task, check **Online homework**, and list distracting sites, for example `youtube.com, tiktok.com`.
5. Use **Start / resume focus** to begin blocking. The Focus page offers a pause button. Closing TaskLock turns site blocking off.

Site blocking is voluntary and browser-specific. The extension calls the local status server at `127.0.0.1:18763`. It does not monitor other webpages, collect browsing history, or phone home. It does not check whether your school has graded or accepted homework.

## Publishing a real installer + website for free

A public GitHub repository with these project files is required. **No GitHub repository was identified during this build, so no public URL exists yet.**

1. Create a new GitHub repository, and upload the **contents** of `TaskLock_v5` at the repository root (the `.github` directory must be included).
2. In repository **Settings → Pages → Source**, select **GitHub Actions**. Push `main` to deploy the `site/` folder via `.github/workflows/website.yml`.
3. In **Actions**, run `TaskLock v5 Windows Installer and Release` manually. The `windows-2022` runner compiles the real `.exe` and installer. The workflow then uploads build artifacts for private testing.
4. **Verify on Windows 11**: launch installer and uninstall, check sounds, test focus extension in Chrome and Edge, test the full-screen reminder and Esc, test backups and v4 migration.
5. When tests pass, publish a GitHub tag `v5.0.0`. The workflow uploads a GitHub Release with `TaskLock-v5.0.0-Setup.exe`, the portable ZIP, and `release-manifest.json` containing real SHA-256 checksums.
6. The GitHub Pages TaskLock site automatically finds the installer using the GitHub Releases API. For Netlify hosting, enter the real `owner/repo` value into `site/release_config.json` prior to upload.
7. On the separate Tavlokyn Studios company website, link the **TaskLock** product card to your published TaskLock site. Add the actual release URL only after it's live. If you're using Base44, you can edit that existing product-card link there manually.

Do not claim the EXE is signed or Windows Smart App Control-compatible unless independently verified. To avoid misleading visitors, the site's Download button stays disabled before a real release asset exists.

## Developer tests

```sh
python -m pytest tests -q
node tests/browser_extension_test.js
xvfb-run -a python tests/gui_smoke.py  # Linux desktop logic smoke test only
```

See `TEST_REPORT.md`, `CHANGELOG.md`, and `RELEASE_CHECKLIST.md`. This is a prototype source release candidate, not a Windows 11-certified production installer.
