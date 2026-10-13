"""Genera el logo de WhisperPRO (onda luminosa sobre squircle violeta) y todos los íconos.

Uso (desde la raíz del repo):   python branding/generar_logo.py
Necesita numpy y pillow. Escribe:
  branding/logo-1024.png · branding/logo.ico · app/logo.ico · app/logo-tray.png
  web/apple-touch-icon.png · web/icon-192.png · web/icon-512.png · web/icon-maskable-512.png

El cuerpo del ícono (violeta con degradé, reflejo, borde de luz y sombra) sale de make_logo() en app/dictado.py.
La onda tiene dos versiones: fina y detallada para tamaños grandes, y simplificada (pocas líneas más gruesas)
para 16–64 px, donde las líneas finas se funden en una mancha.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_logo():
    src = open(os.path.join(RAIZ, "app", "dictado.py"), encoding="utf-8").read()
    a, b = src.index("def make_logo"), src.index("def ensure_icon_file")
    ns = {"np": np}
    exec(src[a:b], ns)
    return ns["make_logo"]


make_logo = _make_logo()

# colores de la onda sobre el violeta: blanco azulado → blanco → blanco rosado
PALETA = [(0.0, (190, 215, 255)), (0.5, (240, 230, 255)), (1.0, (255, 236, 255))]


def _stops(t, pts):
    out = np.zeros(t.shape + (3,), np.float32)
    for i in range(3):
        out[..., i] = np.interp(t, [q[0] for q in pts], [q[1][i] for q in pts])
    return out


def cinta(W, H, n, seed, lw, glow, amp=0.44, env_w=0.30, freqs=(2.0, 3.6, 6.2), core=1.0, scale=2):
    """Cinta de líneas finas que se cruzan (onda luminosa). RGBA con transparencia, afinada en las puntas."""
    rng = np.random.default_rng(seed)
    w, h = W * scale, H * scale
    xs = np.linspace(0, 1, w // 2 + 1)
    env = np.exp(-((xs - 0.5) / env_w) ** 2) * 0.93 + 0.07
    env *= 0.85 + 0.15 * np.sin(2 * np.pi * (xs * 1.3 + rng.random()))
    env *= np.sin(np.pi * xs) ** 0.7
    ph = rng.random(3) * 2 * np.pi
    dens = np.zeros((h, w), np.float32)
    for i in range(n):
        th = np.pi * i / max(1, n - 1)
        y = env * (np.sin(2 * np.pi * freqs[0] * xs + ph[0]) * np.cos(th)
                   + 0.75 * np.sin(2 * np.pi * freqs[1] * xs + ph[1]) * np.sin(th)
                   + 0.30 * np.sin(2 * np.pi * freqs[2] * xs + ph[2] + th))
        pts = [(x * (w - 1), h / 2 + yy * h * amp) for x, yy in zip(xs, y)]
        im = Image.new("L", (w, h), 0)
        ImageDraw.Draw(im).line(pts, fill=int(70 + 50 * np.sin(i * 1.7) ** 2), width=max(1, int(lw * scale)), joint="curve")
        dens += np.asarray(im, np.float32)
    D = np.clip(dens / 255.0, 0, 1.6)
    gx = np.linspace(0, 1, w)[None, :].repeat(h, 0)
    C = _stops(gx, PALETA)
    rgb = C * D[..., None] + (np.clip(D - 0.35, 0, 1) ** 1.6)[..., None] * core * 255
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    out = np.asarray(img, np.float32)
    for k, r in enumerate(glow):
        out = out + np.asarray(img.filter(ImageFilter.GaussianBlur(r * scale)), np.float32) * (0.9 if k == 0 else 0.55)
    out = np.clip(out, 0, 255)
    a = out.max(axis=2, keepdims=True)
    res = np.concatenate([np.where(a > 0, out / np.maximum(a, 1) * 255, 0), a], axis=2).astype(np.uint8)
    return Image.fromarray(res, "RGBA").resize((W, H), Image.LANCZOS)


def onda_simple(size):
    """Versión para 16–64 px: pocas líneas bien marcadas que comparten los puntos de cruce (cinta retorcida),
    con brillo. Se lee como una onda de voz incluso en 16 px."""
    S = size * 12
    fig = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(fig)
    if size >= 48:
        lineas = [(1.0, 0.075, 255), (0.5, 0.040, 190), (-0.5, 0.040, 190), (-1.0, 0.075, 255)]
    else:
        lineas = [(1.0, 0.11, 255), (-1.0, 0.11, 255)]
    for amp, wd, al in lineas:
        pts = []
        for u in np.linspace(0.12, 0.88, 260):
            env = np.exp(-(((u - 0.5) / 0.24) ** 2)) * max(0.0, np.sin(np.pi * (u - 0.12) / 0.76)) ** 0.5
            y = 0.5 + 0.34 * amp * env * np.sin(2 * np.pi * 2.6 * (u - 0.5) + 0.5 * np.pi)   # lóbulo central alto, laterales más bajos
            pts.append((u * S, y * S))
        d.line(pts, fill=al, width=max(2, int(wd * S)), joint="curve")
    glow = fig.filter(ImageFilter.GaussianBlur(S * 0.03))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = Image.new("RGBA", (S, S), (225, 205, 255, 0))
    g.putalpha(glow.point(lambda v: int(v * 0.85)))
    out = Image.alpha_composite(out, g)
    f = Image.new("RGBA", (S, S), (255, 255, 255, 0))
    f.putalpha(fig)
    out = Image.alpha_composite(out, f)
    return out.resize((size, size), Image.LANCZOS)


def logo(size):
    """Logo del tamaño pedido: detallado si hay lugar, simplificado si es chico."""
    body = make_logo(size, bars_on=False)
    if size < 128:
        body.alpha_composite(onda_simple(size))
        return body
    n = 14 if size < 256 else 26 if size < 512 else 44
    lw = 1.6 if size < 256 else 1.5
    rb = cinta(int(size * 0.74), int(size * 0.46), n=n, seed=11, lw=lw if size >= 256 else 1.1, glow=(max(2, size // 256 * 4), max(4, size // 256 * 12)))
    body.alpha_composite(rb, ((size - rb.width) // 2, int(size * 0.5 - rb.height / 2)))
    return body


if __name__ == "__main__":
    grande = logo(1024)
    p = lambda *r: os.path.join(RAIZ, *r)
    grande.save(p("branding", "logo-1024.png"))
    tamanos = [16, 24, 32, 48, 64, 128, 256]
    imgs = {s: logo(s) for s in tamanos}
    base = imgs[256]
    resto = [imgs[s] for s in tamanos if s != 256]
    for destino in (p("app", "logo.ico"), p("branding", "logo.ico")):
        base.save(destino, sizes=[(s, s) for s in tamanos], append_images=resto)
    imgs[64].save(p("app", "logo-tray.png"))
    fondo = (10, 11, 16, 255)

    def sobre_fondo(size, margen=0.0):
        c = Image.new("RGBA", (size, size), fondo)
        inner = int(size * (1 - 2 * margen))
        c.alpha_composite(grande.resize((inner, inner), Image.LANCZOS), ((size - inner) // 2, (size - inner) // 2))
        return c.convert("RGB")

    sobre_fondo(180).save(p("web", "apple-touch-icon.png"))
    sobre_fondo(192).save(p("web", "icon-192.png"))
    sobre_fondo(512).save(p("web", "icon-512.png"))
    sobre_fondo(512, 0.08).save(p("web", "icon-maskable-512.png"))
    print("logo e íconos generados")
