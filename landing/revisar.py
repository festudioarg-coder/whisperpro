"""Chequeo antes de publicar: lista lo que todavía falta completar en la landing.
Uso (desde la raíz del repo):   python landing/revisar.py
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
pend = []
for dp, _, fs in os.walk(RAIZ):
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(dp, f)
        txt = open(p, encoding="utf-8").read()
        rel = os.path.relpath(p, RAIZ)
        for m in re.finditer(r"\[[A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ ]+\]", txt):
            pend.append(f"{rel}: marcador sin completar {m.group(0)}")
        if 'id="descarga-win" href' in txt or re.search(r'id="descarga-win"', txt):
            if re.search(r'<a[^>]*href="#descargar"[^>]*id="descarga-win"', txt):
                pend.append(f"{rel}: el botón 'Descargar para Windows' todavía apunta a #descargar (poné el link del instalador)")
        if "festudios.pro/whisperpro" in txt and "og.png" in txt and not os.path.exists(os.path.join(RAIZ, "img", "og.png")):
            pend.append(f"{rel}: falta img/og.png")
print("\n".join(pend) if pend else "Nada pendiente: se puede publicar.")
sys.exit(1 if pend else 0)
