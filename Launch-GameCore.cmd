@echo off
setlocal
set "GAMECORE_EXE=%~dp0hub\src-tauri\target-json-export\release\gamecore-library.exe"
if not exist "%GAMECORE_EXE%" set "GAMECORE_EXE=%~dp0hub\src-tauri\target\release\gamecore-library.exe"
if not exist "%GAMECORE_EXE%" set "GAMECORE_EXE=%~dp0hub\src-tauri\target\debug\gamecore-library.exe"
if not exist "%GAMECORE_EXE%" set "GAMECORE_EXE=%~dp0hub\src-tauri\target\release\gamecore-hub.exe"
if not exist "%GAMECORE_EXE%" (
  echo GameCore has not been built. See hub\README.md for build instructions.
  pause
  exit /b 1
)
start "" "%GAMECORE_EXE%"
