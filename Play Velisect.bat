@echo off
rem Double-click to play Velisect: the packaged game, built by `npm run package`.
set GAME=%~dp0Packaged\Windows\Velisect.exe
if exist "%GAME%" (
  start "" "%GAME%"
) else (
  echo Velisect is not built yet. Open a terminal in this folder and run:  npm run package
  pause
)
