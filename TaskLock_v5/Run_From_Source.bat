@echo off
cd /d "%~dp0"
py app\TaskLock.py
if errorlevel 1 pause
