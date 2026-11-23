@echo off
setlocal
pushd "%~dp0hub"
call npm run build
if errorlevel 1 goto failed
cargo build --manifest-path src-tauri\Cargo.toml --release --features custom-protocol
if errorlevel 1 goto failed
popd
echo GameCore standalone build is ready. Run Launch-GameCore.cmd.
exit /b 0
:failed
popd
echo GameCore build failed. The launcher was not started.
exit /b 1
