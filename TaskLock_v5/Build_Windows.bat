@echo off
setlocal
cd /d "%~dp0"
echo ======================================
echo       TaskLock v5 BLUECORE Builder
 echo ======================================
where py >nul 2>&1
if not errorlevel 1 (set "PY=py") else (set "PY=python")
%PY% --version
if errorlevel 1 goto fail
%PY% -m pip install pyinstaller
if errorlevel 1 goto fail
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name TaskLock --icon "assets\tasklock.ico" --add-data "assets\tasklock.png;assets" --add-data "app\release_config.json;app" --paths app app\TaskLock.py
if errorlevel 1 goto fail
if not exist "dist\TaskLock.exe" goto fail
if not exist release mkdir release
powershell -NoProfile -Command "Compress-Archive -Path 'dist\TaskLock.exe','Browser_Extension','README.md','CHANGELOG.md','LICENSE' -DestinationPath 'release\TaskLock-v5.0.0-Windows.zip' -Force"
if errorlevel 1 goto fail
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto portable
"%ISCC%" "installer\TaskLock.iss"
if errorlevel 1 goto fail
echo.
echo SUCCESS! Installer: release\TaskLock-v5.0.0-Setup.exe
:portable
echo SUCCESS! Portable EXE: dist\TaskLock.exe
echo Windows ZIP: release\TaskLock-v5.0.0-Windows.zip
echo If installer is missing, install free Inno Setup 6 and run the builder again.
pause
exit /b 0
:fail
echo.
echo Build failed. Copy the error from above for troubleshooting.
pause
exit /b 1
