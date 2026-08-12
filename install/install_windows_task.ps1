# Installs usb-lock as a scheduled task that starts invisibly (no console
# window) in the background on every logon.
#
# Run in PowerShell (does not need to run as Administrator, as long as the
# task only applies to the current user):
#   powershell -ExecutionPolicy Bypass -File install_windows_task.ps1

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $PSScriptRoot
$PythonwExe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonwExe) {
    $PythonwExe = (Get-Command python.exe).Source
    Write-Warning "pythonw.exe not found, using python.exe instead (will show a console window)."
}

$TaskName = "usb-lock"
$Action = New-ScheduledTaskAction -Execute $PythonwExe `
    -Argument "-m usb_lock.gui" `
    -WorkingDirectory $RepoDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description "Locks the screen (or shuts down) on USB removal" -Force

Write-Host "Task '$TaskName' created. It will start automatically on your next logon."
Write-Host "Start it manually now with: Start-ScheduledTask -TaskName '$TaskName'"
