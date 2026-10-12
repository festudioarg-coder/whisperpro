# PyInstaller spec — genera dist/WhisperPRO/WhisperPRO.exe (carpeta, arranque rápido)
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
datas = [(os.path.join(ROOT, "ui"), "ui"), (os.path.join(ROOT, ".env.example"), "."),
         (os.path.join(ROOT, "logo-tray.png"), "."),                  # ícono de la bandeja
         (os.path.join(ROOT, "licencia_clave_publica.txt"), ".")]     # sin esto nadie podría activar Pro
datas += collect_data_files("webview")
datas += collect_data_files("sounddevice")
hidden = collect_submodules("webview") + collect_submodules("pystray") + ["PIL._tkinter_finder", "comtypes"]

a = Analysis([os.path.join(ROOT, "dictado.py")], pathex=[ROOT], datas=datas, hiddenimports=hidden,
             excludes=["faster_whisper", "ctranslate2", "torch", "tkinter", "matplotlib", "scipy", "pandas"],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="WhisperPRO", console=False,
          icon=os.path.join(ROOT, "logo.ico") if os.path.exists(os.path.join(ROOT, "logo.ico")) else None,
          version=os.path.join(ROOT, "build", "version_info.txt"),
          disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="WhisperPRO")
