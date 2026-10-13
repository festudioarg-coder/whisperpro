"""Herramienta de FESTUDIOS para licencias Pro de WhisperPRO. NO se distribuye con la app.

  python herramientas/licencias.py claves                         crea tu par de claves (una sola vez)
  python herramientas/licencias.py emitir --email a@b.com         licencia Pro sin vencimiento
  python herramientas/licencias.py emitir --email a@b.com --dias 365
  python herramientas/licencias.py verificar licencias-emitidas/a_b.com.json

La clave PRIVADA se guarda en  ~/.whisperpro/clave_privada.key  (fuera del repo). Quien la tenga puede emitir
licencias: hacé copia en tu gestor de contraseñas y no la subas nunca a git. La clave PÚBLICA se escribe en
app/licencia_clave_publica.txt (esa sí va en el repo y en la app).
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app"))
import licencia as L  # noqa: E402

PRIVADA = os.path.join(os.path.expanduser("~"), ".whisperpro", "clave_privada.key")
SALIDA = os.path.join(RAIZ, "licencias-emitidas")


def cmd_claves(_):
    if os.path.exists(PRIVADA):
        print(f"Ya existe una clave privada en {PRIVADA}. No la piso (perderías la capacidad de emitir licencias válidas).")
        return 1
    os.makedirs(os.path.dirname(PRIVADA), exist_ok=True)
    secreta = os.urandom(32)
    with open(PRIVADA, "w", encoding="utf-8") as f:
        f.write(secreta.hex())
    try:
        os.chmod(PRIVADA, 0o600)
    except OSError:
        pass
    publica = L.clave_publica(secreta).hex()
    with open(L.ARCHIVO_PUBLICA, "w", encoding="utf-8") as f:
        f.write(publica + "\n")
    print("Clave privada guardada en:", PRIVADA, "(hacé una copia segura; NO la subas a git)")
    print("Clave pública escrita en:", L.ARCHIVO_PUBLICA)
    print("Ahora: git add app/licencia_clave_publica.txt && git commit -m \"Clave pública de licencias\" && git push")
    return 0


def cmd_emitir(a):
    if not os.path.exists(PRIVADA):
        print("Primero creá tus claves:  python herramientas/licencias.py claves")
        return 1
    secreta = bytes.fromhex(open(PRIVADA, encoding="utf-8").read().strip())
    if L.clave_publica(secreta).hex() != L._publica_hex():
        print("La clave privada no corresponde a app/licencia_clave_publica.txt. Las licencias no se podrían activar.")
        return 1
    lic = L.emitir(secreta, a.email, dias=a.dias)
    ok, res = L.verificar(lic)
    if not ok:
        print("La licencia emitida no pasó la verificación:", res)
        return 1
    os.makedirs(SALIDA, exist_ok=True)
    nombre = re.sub(r"[^a-z0-9._-]+", "_", lic["email"]) + ".json"
    ruta = a.salida or os.path.join(SALIDA, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(lic, f, ensure_ascii=False, indent=2)
    print(json.dumps(lic, ensure_ascii=False, indent=2))
    print(f"\nGuardada en {ruta}\nEnviásela a la persona: pega el contenido en WhisperPRO → Ajustes → Activar Pro.")
    return 0


def cmd_verificar(a):
    ok, res = L.verificar(open(a.archivo, encoding="utf-8").read())
    print("VÁLIDA:" if ok else "NO VÁLIDA:", res)
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("claves").set_defaults(f=cmd_claves)
    e = sub.add_parser("emitir"); e.add_argument("--email", required=True); e.add_argument("--dias", type=int); e.add_argument("--salida"); e.set_defaults(f=cmd_emitir)
    v = sub.add_parser("verificar"); v.add_argument("archivo"); v.set_defaults(f=cmd_verificar)
    args = ap.parse_args()
    sys.exit(args.f(args))
