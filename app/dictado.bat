@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo Falta el entorno: corre instalar.bat primero & pause & exit /b 1)
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im WhisperPRO.exe >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'dictado\.py|dev\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
call venv\Scripts\activate
python dictado.py
pause
