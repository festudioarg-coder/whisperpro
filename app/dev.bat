@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (echo Falta el entorno: corre instalar.bat primero & pause & exit /b 1)
taskkill /f /im pythonw.exe >nul 2>&1
call venv\Scripts\activate
python dev.py
pause
