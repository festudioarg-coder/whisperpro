@echo off
rem Genera el instalador: build\out\WhisperPRO-Setup-<version>.exe
rem Requiere: instalar.bat corrido antes; Inno Setup 6 (jrsoftware.org/isdl.php) para el .exe de setup.
rem Firma opcional: definí WP_CERT (ruta del .pfx) y WP_CERT_PASS, o WP_CERT_SHA1 (huella de un cert instalado).
cd /d "%~dp0"
call venv\Scripts\activate
pip install -q pyinstaller
for /f "tokens=1* delims==" %%a in ('python build\version_info.py') do if "%%a"=="WP_VERSION" set WP_VERSION=%%b
echo [build] version %WP_VERSION%
python -c "import dictado; dictado.ensure_icon_file()"
if not exist logo.ico (echo FALLO: no se pudo generar logo.ico & pause & exit /b 1)
rmdir /s /q build\work dist 2>nul
pyinstaller --noconfirm --clean --workpath build\work --distpath dist build\WhisperPRO.spec || (echo FALLO pyinstaller & pause & exit /b 1)
echo [build] dist\WhisperPRO\WhisperPRO.exe listo
echo [build] autoprueba del programa empaquetado...
del "%APPDATA%\WhisperPRO\selftest.txt" 2>nul
start /wait "" "dist\WhisperPRO\WhisperPRO.exe" --selftest
set ST=%errorlevel%
if exist "%APPDATA%\WhisperPRO\selftest.txt" type "%APPDATA%\WhisperPRO\selftest.txt"
if not "%ST%"=="0" (echo FALLO la autoprueba: el instalador NO se genera. Mira las lineas FALLA de arriba. & pause & exit /b 1)
call :sign "dist\WhisperPRO\WhisperPRO.exe"
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
  %ISCC% build\instalador.iss || (echo FALLO Inno Setup & pause & exit /b 1)
  for %%f in (build\out\WhisperPRO-Setup-*.exe) do call :sign "%%f"
  echo.
  echo ============================================================
  echo  INSTALADOR LISTO:  build\out\WhisperPRO-Setup-%WP_VERSION%.exe
  echo ============================================================
  explorer build\out
) else (
  echo Inno Setup no esta instalado: solo quedo dist\WhisperPRO. Instala Inno Setup 6 y volve a correr build.bat.
)
pause
exit /b 0

:sign
set SIGNTOOL=
for /f "delims=" %%p in ('dir /b /s /o-n "%ProgramFiles(x86)%\Windows Kits\10\bin\*\x64\signtool.exe" 2^>nul') do if not defined SIGNTOOL set SIGNTOOL=%%p
if not defined SIGNTOOL (echo [firma] signtool no encontrado: se omite la firma de %~1 & exit /b 0)
if defined WP_CERT (
  "%SIGNTOOL%" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "%WP_CERT%" /p "%WP_CERT_PASS%" /d "WhisperPRO" %1 && echo [firma] firmado %~1
) else if defined WP_CERT_SHA1 (
  "%SIGNTOOL%" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /sha1 %WP_CERT_SHA1% /d "WhisperPRO" %1 && echo [firma] firmado %~1
) else (
  echo [firma] sin certificado configurado: se omite la firma de %~1
)
exit /b 0
