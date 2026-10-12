@echo off
rem Crea un acceso directo en Inicio de Windows para que arranque solo, sin consola.
set "SRC=%~dp0dictado_silencioso.vbs"
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WhisperPRO.lnk"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%');$s.TargetPath='%SRC%';$s.IconLocation='%~dp0logo.ico';$s.Save()"
echo Listo: WhisperPRO va a arrancar con Windows (icono en la bandeja). Para quitarlo, borra el acceso directo en:
echo %LNK%
pause
