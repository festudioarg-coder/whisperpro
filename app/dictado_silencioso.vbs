' Arranca WhisperPRO sin consola (queda en la bandeja). Cierra una instancia previa si la hay.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.Run "taskkill /f /im pythonw.exe", 0, True
sh.Run """" & dir & "\venv\Scripts\pythonw.exe"" """ & dir & "\dictado.py""", 0, False
