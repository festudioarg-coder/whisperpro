@echo off
cd /d "%~dp0"
echo [WhisperPRO] preparando entorno...
if not exist venv\Scripts\python.exe (
  python -m venv venv || (echo Necesitas Python 3.10+ de python.org, con "Add to PATH" & pause & exit /b 1)
)
call venv\Scripts\activate
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
echo.
echo Listo. Si es la primera vez: abri .env y pega tu GROQ_API_KEY. Despues: dictado.bat (o dev.bat para desarrollar).
pause
