"""Modo desarrollo: corre dictado.py con consola y lo reinicia solo cuando cambia
dictado.py, .env o algo en ui/. Así cada parche se ve al instante sin cerrar nada."""
import os, sys, time, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
WATCH = ["dictado.py", "hotkeys.py", ".env", "ui"]


def snapshot():
    out = {}
    for w in WATCH:
        p = os.path.join(BASE, w)
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    fp = os.path.join(root, f)
                    out[fp] = os.path.getmtime(fp)
        elif os.path.exists(p):
            out[p] = os.path.getmtime(p)
    return out


def run():
    env = dict(os.environ, DICTADO_DEBUG=os.environ.get("DICTADO_DEBUG", "1"), PYTHONUTF8="1")
    return subprocess.Popen([sys.executable, os.path.join(BASE, "dictado.py")], cwd=BASE, env=env)


print("[dev] modo desarrollo: reinicia solo al guardar dictado.py / .env / ui/*. Ctrl+C para salir.", flush=True)
snap = snapshot()
proc = run()
try:
    while True:
        time.sleep(0.7)
        if proc.poll() is not None:
            print(f"[dev] el programa terminó (código {proc.returncode}). Esperando un cambio para reiniciar...", flush=True)
            while snapshot() == snap:
                time.sleep(0.7)
        now = snapshot()
        if now != snap:
            snap = now
            print("\n[dev] cambio detectado → reiniciando\n", flush=True)
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            time.sleep(0.4)
            proc = run()
except KeyboardInterrupt:
    if proc.poll() is None:
        proc.kill()
