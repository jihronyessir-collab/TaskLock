# TaskLock v5.1.1 — BLUECORE / Color & Sound

**Publisher brand:** Tavlokyn Studios  
**Product slogan:** Stay Focused. Finish Strong.  
**Status:** V5.1.1 Windows public beta. The updated application and installer are published through official GitHub Releases. Beta testing continues.  
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
| Sounds | 12 generated WAV melodies, custom PCM WAV, category sounds, volume | Actual device behavior still needs ongoing beta feedback |
| Preferences | 9 palettes, text size, reduced-motion preference, timer settings | Some accent panels retain the BLUECORE color |
| Storage | Auto pre-v5 copy, backup ZIP and restore | No sync or cloud account |
| Updates | In-app changelog, GitHub release checker and download prompt | Uses GitHub Releases and official GitHub Pages fallback; downloads require user approval |
| Windows distribution | PyInstaller portable EXE builder + Inno Setup installer + GitHub Actions | Automated Windows build passes; continue real-world beta testing |
| TaskLock website | Static free website with a download button linked to actual published releases | Public on GitHub Pages |

## Try the app on Windows 11 with Python already installed

1. Extract the `TaskLock_v5_Source_and_Website.zip` archive.
2. Open `TaskLock_v5` and double-click `Run_From_Source.bat` (Python 3.10+ with Tkinter required).
3. If you used TaskLock v4, v5 reads `%APPDATA%\TaskLock\tasks.json` and makes a snapshot in `%APPDATA%\TaskLock\pre_v5_backup` before loading existing data.
4. In **Tasks**, add your assignment and optional subtasks. In **Focus**, start a session.
5. In **Settings**, export a ZIP backup before experimenting further.

### Build the Windows EXE and installer locally

1. Double-click `Build_Windows.bat` (requires Python and internet to install the free PyInstaller build tool).
2. It creates `dist\TaskLock.exe` and `release\TaskLock-v5.1.1-Windows.zip`.
3. For the **actual Windows installer**, also install free [Inno Setup 6](https://jrsoftware.org/isinfo.php), then rerun the build script.
4. When successful, `release\TaskLock-v5.1.1-Setup.exe` appears. This installer creates Start Menu shortcuts and an optional desktop shortcut. It installs per-user and does **not** erase `%APPDATA%\TaskLock` on uninstall.

**Security note:** Unsigned software may be blocked by Windows Smart App Control. Do not turn off Smart App Control just to use TaskLock. Instead, have the release built, tested, and eventually code-signed by the publisher.

### Enable Chrome / Edge website blocking

1. Keep TaskLock open.
2. Chrome: visit `chrome://extensions`; Edge: `edge://extensions`.
3. Enable Developer mode; choose **Load unpacked**, then choose `Browser_Extension` from the extracted source, portable ZIP, or installed program folder.
4. Add a task, check **Online homework**, and list distracting sites, for example `youtube.com, tiktok.com`.
5. Use **Start / resume focus** to begin blocking. The Focus page offers a pause button. Closing TaskLock turns site blocking off.

Site blocking is voluntary and browser-specific. The extension calls the local status server at `127.0.0.1:18763`. It does not monitor other webpages, collect browsing history, or phone home. It does not check whether your school has graded or accepted homework.

## Official public Windows beta

The Windows installer is published through the official
[TaskLock GitHub Releases](https://github.com/jihronyessir-collab/TaskLock/releases).
The current patch release is **v5.1.1**, which fixes the Check for Updates
HTTP 404 issue by falling back to an official release feed hosted on
[TaskLock GitHub Pages](https://jihronyessir-collab.github.io/TaskLock/).

- The **Check for Updates** button checks GitHub Releases first, then the official
  GitHub Pages release feed if GitHub's API is unavailable.
- TaskLock **asks permission before downloading** an update. Downloaded installers
  are not installed automatically.
- The app validates installer names, version numbers, download URLs, and sizes.
  SHA-256 hashes are checked when the release metadata provides them.
- Existing installations with the broken checker should download and run the
  v5.1.1 installer manually once. Local AppData task data is preserved by design;
  making a backup before upgrading is recommended.
- Windows installers are not currently code-signed. Do not disable security
  protections to install software; verify the publisher and release source.

### Publishing future releases

1. Update `VERSION` in `app/tasklock_core.py`, and the installer version in
   `installer/TaskLock.iss`.
2. Update the changelog and test the new features.
3. GitHub Actions builds and tests the real Windows app and installer.
4. After verification, use the release workflow's explicit publish option.
5. The release workflow refreshes the GitHub Pages release feed automatically.
6. Update the Tavlokyn Studios product download link to the published installer.

## Developer tests

```sh
python -m pytest tests -q
node tests/browser_extension_test.js
xvfb-run -a python tests/gui_smoke.py  # Linux desktop logic smoke test only
```

See `TEST_REPORT.md`, `CHANGELOG.md`, and `RELEASE_CHECKLIST.md`. This is a public beta, not a Windows 11-certified or code-signed production installer.
