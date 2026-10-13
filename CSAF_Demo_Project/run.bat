@echo off
rem Double-click launcher for the Nozama demo. See run.ps1 for details.
powershell.exe -NoLogo -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
if errorlevel 1 (
  echo.
  echo Startup failed. See the message above.
  pause
)
