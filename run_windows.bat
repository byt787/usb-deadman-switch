@echo off
REM Manueller Start zum Testen (zeigt ein Konsolenfenster mit Logs).
cd /d "%~dp0"
python -m usb_lock.main
pause
