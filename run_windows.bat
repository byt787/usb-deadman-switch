@echo off
REM Manual test run (shows a console window with logs).
cd /d "%~dp0"
python -m usb_lock.main
pause
