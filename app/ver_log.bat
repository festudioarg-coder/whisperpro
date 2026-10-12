@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Get-Content -Path '.\dictado.log' -Tail 80"
pause
