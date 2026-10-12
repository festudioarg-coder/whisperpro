"""Motor de atajos de WhisperPRO.

No depende de Windows ni de la librería `keyboard`: recibe eventos de teclas (nombre, scancode, bajó/subió)
y decide si se dejan pasar o se tragan. Así se puede probar en cualquier sistema (ver tests/test_hotkeys.py).

Qué maneja:
  · hasta 2 atajos de grabación (modo "toggle": el atajo empieza y la tecla principal sola corta;
    modo "hold": se graba mientras mantenés el atajo)
  · 2 atajos de captura de pantalla (región y pantalla completa), cada uno opcional
  · historial y deshacer, que usan el mismo modificador del primer atajo de grabación (Win+H, Win+Z)
  · "capturar combinación": para elegir un atajo desde el panel apretándolo
"""
import threading

CAPS = "caps lock"
MODS = ("win", "ctrl", "alt", "shift")
MOD_ORDER = ("win", "ctrl", "alt", "shift", CAPS)

_SC = {57: "space", 1: "esc", 58: CAPS, 91: "win", 92: "win", 29: "ctrl", 42: "shift", 54: "shift", 56: "alt"}
_ALIAS = {
    "espacio": "space", "windows": "win", "left windows": "win", "right windows": "win", "cmd": "win", "super": "win",
    "left ctrl": "ctrl", "right ctrl": "ctrl", "control": "ctrl", "left alt": "alt", "right alt": "alt",
    "alt gr": "alt", "left shift": "shift", "right shift": "shift", "escape": "esc",
    "caps": CAPS, "capslock": CAPS, "bloq mayús": CAPS, "bloq mayus": CAPS,
    "imprimir pantalla": "print screen", "prtsc": "print screen", "prtscn": "print screen", "print_screen": "print screen",
}
# teclas que se pueden usar solas (sin modificador) sin romper la escritura normal
_SOLO_OK = {"print screen", "pause", "scroll lock"} | {f"f{i}" for i in range(1, 25)}
# combinaciones de Windows que no se pisan
RESERVED = {"ctrl+alt+delete", "win+l", "win+d", "win+e", "win+r", "alt+tab", "alt+f4",
            "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+a", "ctrl+shift+esc"}


def canon(name, scan=None):
    """Nombre único para una tecla, sin importar izquierda/derecha ni el idioma del teclado."""
    if scan in _SC:
        return _SC[scan]
    n = (name or "").strip().lower()
    return _ALIAS.get(n, n)


def is_mod(k):
    return k in MODS or k == CAPS


def parse_combo(combo):
    """'win+space' -> (frozenset({'win'}), 'space'). Devuelve (mods, main, error)."""
    parts = [canon(p) for p in (combo or "").split("+") if p.strip()]
    if not parts:
        return frozenset(), None, "Falta elegir la combinación"
    mods = frozenset(k for k in parts if is_mod(k))
    mains = [k for k in parts if not is_mod(k)]
    if not mains:
        return mods, None, "Falta una tecla además del modificador"
    if len(mains) > 1:
        return mods, None, "Solo una tecla además de los modificadores (Win, Ctrl, Alt, Shift)"
    return mods, mains[0], None


def format_combo(mods, main):
    return "+".join([m for m in MOD_ORDER if m in mods] + [main])


def pretty(combo):
    names = {"win": "Win", "ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", CAPS: "Bloq Mayús", "space": "Espacio",
             "print screen": "Impr Pant", "esc": "Esc", "enter": "Enter", "tab": "Tab"}
    return " + ".join(names.get(p, p.upper() if len(p) == 1 else p.capitalize()) for p in (combo or "").split("+") if p)


class Binding:
    def __init__(self, bid, action, combo=None, mode="toggle", mods=None, main=None):
        self.id, self.action, self.mode = bid, action, mode
        if combo is not None:
            self.mods, self.main, self.error = parse_combo(combo)
        else:
            self.mods, self.main, self.error = frozenset(mods or ()), main, None
        self.keys = frozenset(self.mods | ({self.main} if self.main else set()))

    @property
    def combo(self):
        return format_combo(self.mods, self.main) if self.main else ""


# ---------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------
def default_settings(legacy_hotkey="win+space"):
    """El primer atajo sale de DICTADO_HOTKEY (compatibilidad): Win+... corta con la tecla sola; el resto se mantiene."""
    mods, main, err = parse_combo(legacy_hotkey)
    if err:
        legacy_hotkey, mods = "win+space", frozenset({"win"})
    mode = "toggle" if "win" in mods else "hold"
    return {"rec": [{"combo": canon_combo(legacy_hotkey), "mode": mode}],
            "shot_region": {"combo": "win+shift+s", "enabled": False},
            "shot_full": {"combo": "print screen", "enabled": False},
            "shot_save": True}


def canon_combo(combo):
    mods, main, err = parse_combo(combo)
    return "" if err else format_combo(mods, main)


def normalize_settings(raw, legacy_hotkey="win+space"):
    base = default_settings(legacy_hotkey)
    if not isinstance(raw, dict):
        return base
    out = {"rec": [], "shot_region": dict(base["shot_region"]), "shot_full": dict(base["shot_full"]),
           "shot_save": bool(raw.get("shot_save", True))}
    for r in (raw.get("rec") or [])[:2]:
        if isinstance(r, dict) and r.get("combo"):
            out["rec"].append({"combo": canon_combo(r["combo"]) or str(r["combo"]).lower(),
                               "mode": "hold" if r.get("mode") == "hold" else "toggle"})
    if not out["rec"] and "rec" not in raw:
        out["rec"] = base["rec"]
    for k in ("shot_region", "shot_full"):
        v = raw.get(k)
        if isinstance(v, dict):
            out[k] = {"combo": canon_combo(v.get("combo", "")) or str(v.get("combo", "")).lower() or base[k]["combo"],
                      "enabled": bool(v.get("enabled"))}
    return out


def validate(cfg, history_key="h"):
    """Devuelve (ok, mensaje). Revisa combinaciones inválidas, repetidas o que chocan con Windows."""
    seen = {}
    items = [("rec%d" % (i + 1), "Atajo de grabación %d" % (i + 1), r["combo"]) for i, r in enumerate(cfg.get("rec", []))]
    if not items:
        return False, "Tiene que haber al menos un atajo de grabación"
    for k, label in (("shot_region", "Captura de región"), ("shot_full", "Captura de pantalla completa")):
        if cfg.get(k, {}).get("enabled"):
            items.append((k, label, cfg[k]["combo"]))
    for bid, label, combo in items:
        mods, main, err = parse_combo(combo)
        if err:
            return False, "%s: %s" % (label, err)
        c = format_combo(mods, main)
        if main == "esc":
            return False, "%s: Esc está reservada para cancelar la grabación" % label
        if not mods and main not in _SOLO_OK:
            return False, "%s: sola esa tecla rompería la escritura; sumale Win, Ctrl, Alt o Shift" % label
        if c in RESERVED:
            return False, "%s: %s ya la usa Windows" % (label, pretty(c))
        if c in seen:
            return False, "%s y %s tienen la misma combinación (%s)" % (seen[c], label, pretty(c))
        seen[c] = label
    # historial y deshacer salen del modificador del primer atajo de grabación
    first = parse_combo(cfg["rec"][0]["combo"])[0] or frozenset({"ctrl", "alt"})
    for name, key in (("Historial", history_key), ("Deshacer", "z")):
        c = format_combo(first, key)
        if c in seen:
            return False, "%s choca con %s (%s)" % (seen[c], name, pretty(c))
    return True, ""


def build_bindings(cfg, history_key="h"):
    out = []
    for i, r in enumerate(cfg.get("rec", [])[:2]):
        out.append(Binding("rec%d" % (i + 1), "rec", r["combo"], r.get("mode", "toggle")))
    for k, action in (("shot_region", "shot_region"), ("shot_full", "shot_full")):
        v = cfg.get(k) or {}
        if v.get("enabled") and v.get("combo"):
            out.append(Binding(k, action, v["combo"]))
    first = next((b for b in out if b.action == "rec" and b.main), None)
    base = first.mods if first and first.mods else frozenset({"ctrl", "alt"})
    out.append(Binding("history", "history", mods=base, main=history_key))
    out.append(Binding("undo", "undo", mods=base, main="z"))
    return [b for b in out if b.main]


# ---------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------
class HotkeyEngine:
    """cb necesita: start(binding), stop(), is_recording(), esc(down), shot(kind), history(), undo(),
    win_used(), send_caps(). Todo lo lento (abrir el micrófono, capturar) lo hace cb en otro hilo:
    on_event corre dentro del hook del teclado y NO puede bloquear."""

    def __init__(self, cb, bindings=()):
        self.cb = cb
        self._lock = threading.RLock()
        self.down, self.swallowed = set(), set()
        self.win_used, self.caps_used = False, False
        self.active = None
        self.cap = None
        self.bindings, self.caps_mod = [], False
        self.set_bindings(bindings)

    def set_bindings(self, bindings):
        with self._lock:
            self.bindings = list(bindings)
            self.caps_mod = any(CAPS in b.mods for b in self.bindings)

    # ---- eventos ----
    def on_event(self, name, scan, down):
        """True = dejar pasar la tecla; False = tragarla."""
        k = canon(name, scan)
        with self._lock:
            if self.cap is not None:
                return self._capture_event(k, down)
            return self._event(k, down)

    def _event(self, k, down):
        repeat = down and k in self.down
        if down:
            self.down.add(k)
        else:
            self.down.discard(k)
        if self.active and not self.cb.is_recording():
            self.active = None                      # la grabación terminó por otro camino (Esc, error, botón)

        if k == "win" and down and not repeat:
            self.win_used = False

        if k == "esc":
            if self.cb.is_recording():
                self.cb.esc(down)                   # el Esc no le llega a la app mientras grabás
                return False
            return True

        # modo "mantener": se corta al soltar cualquier tecla del atajo
        if self.active and self.active.mode == "hold" and not down and k in self.active.keys:
            self.active = None
            self.cb.stop()

        if k == CAPS and self.caps_mod:
            if down:
                if not repeat:
                    self.caps_used = False
                return False
            if not self.caps_used and not self.active:
                self.cb.send_caps()                 # Bloq Mayús tocada sola: funciona como siempre
            return False

        if k in self.swallowed:                      # la suelta (y las repeticiones) de una tecla que ya tragamos
            if not down:
                self.swallowed.discard(k)
            return False

        if not down or repeat:
            return True

        # modo "pulsar": la tecla principal sola corta la grabación
        if self.active and self.active.mode == "toggle" and k == self.active.main:
            self.active = None
            self.swallowed.add(k)
            self.cb.stop()
            return False

        if is_mod(k):
            return True
        mods_down = frozenset(x for x in self.down if is_mod(x) and x != k)
        for b in self.bindings:
            if b.main == k and b.mods == mods_down:
                return self._fire(b, k)
        return True

    def _fire(self, b, k):
        if "win" in b.mods and not self.win_used:
            self.win_used = True
            self.cb.win_used()                       # evita que al soltar Win se abra el menú Inicio
        if CAPS in b.mods:
            self.caps_used = True
        self.swallowed.add(k)
        if b.action == "rec":
            if not self.cb.is_recording():
                self.active = b
                self.cb.start(b)
        elif b.action in ("shot_region", "shot_full"):
            self.cb.shot("region" if b.action == "shot_region" else "full")
        elif b.action == "history":
            self.cb.history()
        elif b.action == "undo":
            self.cb.undo()
        return False

    # ---- capturar una combinación (para elegirla desde el panel) ----
    def _capture_event(self, k, down):
        c = self.cap
        if down:
            if k == "esc" and not c["keys"]:
                c["result"] = {"cancel": True}
                c["ev"].set()
                return False
            if k not in c["keys"]:
                c["keys"].append(k)
            c["pressed"].add(k)
        else:
            c["pressed"].discard(k)
            mains = [x for x in c["keys"] if not is_mod(x)]
            if mains and (not c["pressed"] or k in mains):
                mods = frozenset(x for x in c["keys"] if is_mod(x))
                c["result"] = {"combo": format_combo(mods, mains[-1])}
                c["ev"].set()
            elif not c["pressed"]:
                c["keys"].clear()                    # soltó solo modificadores: empieza de nuevo
        return False

    def capture(self, timeout=10.0):
        ev = threading.Event()
        with self._lock:
            if self.cap is not None:
                return {"error": "Ya hay una captura en curso"}
            self.cap = {"keys": [], "pressed": set(), "result": None, "ev": ev}
        ok = ev.wait(timeout)
        with self._lock:
            res = self.cap["result"] if ok else {"timeout": True}
            self.cap = None
            self.down.clear()
            self.swallowed.clear()
        return res
