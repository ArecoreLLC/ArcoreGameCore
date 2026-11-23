@echo off
setlocal
set "GAMECORE_EXE=%~dp0hub\src-tauri\target\release\gamecore-library.exe"
if not exist "%GAMECORE_EXE%" (
  echo GameCore standalone build is missing. Run Build-GameCore.cmd first.
  pause
  exit /b 1
)
start "" /D "%~dp0hub" "%GAMECORE_EXE%"
