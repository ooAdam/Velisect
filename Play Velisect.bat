@echo off
rem Double-click to play Velisect: the packaged game, built by `npm run package` into %LOCALAPPDATA%\Velisect.
set GAME=%LOCALAPPDATA%\Velisect\Packaged\Windows\Velisect.exe
if exist "%GAME%" (
  start "" "%GAME%"
) else (
  echo Velisect is not built yet. Open a terminal in the project folder and run:  npm run package
  pause
)
