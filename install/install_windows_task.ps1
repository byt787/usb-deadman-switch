# Installiert usb-lock als geplante Aufgabe, die bei jeder Anmeldung
# unsichtbar (ohne Konsolenfenster) im Hintergrund startet.
#
# Ausfuehren in einer PowerShell (muss nicht als Administrator laufen,
# solange der Task nur fuer den aktuellen Benutzer gilt):
#   powershell -ExecutionPolicy Bypass -File install_windows_task.ps1

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $PSScriptRoot
$PythonwExe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonwExe) {
    $PythonwExe = (Get-Command python.exe).Source
    Write-Warning "pythonw.exe nicht gefunden, verwende python.exe (zeigt ein Konsolenfenster)."
}

$TaskName = "usb-lock"
$Action = New-ScheduledTaskAction -Execute $PythonwExe `
    -Argument "-m usb_lock.gui" `
    -WorkingDirectory $RepoDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description "Sperrt den Bildschirm bei USB-Entfernung" -Force

Write-Host "Task '$TaskName' wurde angelegt. Er startet bei der naechsten Anmeldung automatisch."
Write-Host "Manuell jetzt starten mit: Start-ScheduledTask -TaskName '$TaskName'"
