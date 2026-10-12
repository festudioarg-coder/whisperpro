"""Pruebas del motor de atajos (sin Windows). Correr:  python -m unittest discover -s tests   (desde app/)"""
import os, sys, threading, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hotkeys as H


class CB:
    def __init__(self):
        self.calls, self.recording = [], False
    def start(self, b): self.calls.append(("start", b.id)); self.recording = True
    def stop(self): self.calls.append(("stop",)); self.recording = False
    def is_recording(self): return self.recording
    def esc(self, down): self.calls.append(("esc", down))
    def shot(self, kind): self.calls.append(("shot", kind))
    def history(self): self.calls.append(("history",))
    def undo(self): self.calls.append(("undo",))
    def win_used(self): self.calls.append(("win_used",))
    def send_caps(self): self.calls.append(("caps",))


def eng(rec=None, **extra):
    cfg = H.default_settings("win+space")
    if rec is not None:
        cfg["rec"] = rec
    cfg.update(extra)
    cb = CB()
    return H.HotkeyEngine(cb, H.build_bindings(cfg)), cb


def press(e, *keys):
    """Devuelve lista de (tecla, pasa?) para una secuencia 'k' (baja) / '^k' (sube)."""
    out = []
    for k in keys:
        up = k.startswith("^")
        name = k[1:] if up else k
        out.append((name, e.on_event(name, None, not up)))
    return out


def passed(res): return {k: v for k, v in res}


class Toggle(unittest.TestCase):
    def test_win_space_empieza_y_space_corta(self):
        e, cb = eng()
        r = press(e, "left windows", "space")
        self.assertEqual(r, [("left windows", True), ("space", False)])           # Win pasa, Space se traga
        self.assertEqual(cb.calls, [("win_used",), ("start", "rec1")])
        press(e, "^space", "^left windows")                                        # soltó todo; sigue grabando
        self.assertTrue(cb.recording)
        r = press(e, "space")                                                      # Space solo corta
        self.assertEqual(r, [("space", False)])
        self.assertEqual(cb.calls[-1], ("stop",))
        self.assertEqual(press(e, "^space"), [("^space".lstrip("^"), False)])      # y no deja pasar la suelta
        self.assertEqual(press(e, "space", "^space"), [("space", True), ("space", True)])  # después Space es Space

    def test_repeticion_no_corta(self):
        e, cb = eng()
        press(e, "windows", "space")
        n = len(cb.calls)
        self.assertEqual(press(e, "space", "space", "space"), [("space", False)] * 3)   # autorepetición: se traga, no actúa
        self.assertEqual(len(cb.calls), n)

    def test_modificadores_exactos(self):
        e, cb = eng()
        press(e, "windows", "shift", "space")
        self.assertEqual(cb.calls, [])                                             # Win+Shift+Space no es Win+Space
        self.assertTrue(passed(press(e, "^space", "^shift", "^windows"))["^space".lstrip("^")])

    def test_win_used_una_vez_por_pulsacion(self):
        e, cb = eng()
        press(e, "windows", "h")
        press(e, "^h", "z")
        self.assertEqual([c for c in cb.calls if c == ("win_used",)], [("win_used",)])
        self.assertIn(("history",), cb.calls); self.assertIn(("undo",), cb.calls)

    def test_grabacion_terminada_por_otro_camino(self):
        e, cb = eng()
        press(e, "windows", "space", "^space", "^windows")
        cb.recording = False                                                       # p. ej. se descartó con Esc
        press(e, "windows", "space")
        self.assertEqual([c for c in cb.calls if c[0] == "start"], [("start", "rec1"), ("start", "rec1")])


class Hold(unittest.TestCase):
    def test_caps_space_mantener(self):
        e, cb = eng(rec=[{"combo": "caps lock+space", "mode": "hold"}])
        r = press(e, "caps lock", "space")
        self.assertEqual(r, [("caps lock", False), ("space", False)])
        self.assertEqual(cb.calls, [("start", "rec1")])
        press(e, "^space")
        self.assertEqual(cb.calls[-1], ("stop",))
        press(e, "^caps lock")
        self.assertNotIn(("caps",), cb.calls)                                      # se usó como modificador: no cambia mayúsculas

    def test_caps_sola_sigue_funcionando(self):
        e, cb = eng(rec=[{"combo": "caps lock+space", "mode": "hold"}])
        press(e, "caps lock", "^caps lock")
        self.assertEqual(cb.calls, [("caps",)])

    def test_soltar_el_modificador_tambien_corta(self):
        e, cb = eng(rec=[{"combo": "ctrl+alt+d", "mode": "hold"}])
        press(e, "ctrl", "alt", "d")
        self.assertEqual(cb.calls, [("start", "rec1")])
        press(e, "^ctrl")
        self.assertEqual(cb.calls[-1], ("stop",))


class Dos(unittest.TestCase):
    def test_dos_atajos_de_grabacion(self):
        e, cb = eng(rec=[{"combo": "win+space", "mode": "toggle"}, {"combo": "ctrl+alt+d", "mode": "hold"}])
        press(e, "ctrl", "alt", "d")
        self.assertEqual(cb.calls, [("start", "rec2")])
        press(e, "^d")
        self.assertEqual(cb.calls[-1], ("stop",))
        press(e, "^alt", "^ctrl", "windows", "space")
        self.assertEqual(cb.calls[-1], ("start", "rec1"))

    def test_historial_usa_el_modificador_del_primero(self):
        e, cb = eng(rec=[{"combo": "ctrl+alt+d", "mode": "toggle"}])
        press(e, "ctrl", "alt", "h")
        self.assertEqual(cb.calls, [("history",)])


class Capturas(unittest.TestCase):
    def test_print_screen_y_win_shift_s(self):
        e, cb = eng(shot_full={"combo": "print screen", "enabled": True},
                    shot_region={"combo": "win+shift+s", "enabled": True})
        self.assertEqual(press(e, "print screen"), [("print screen", False)])
        press(e, "^print screen", "windows", "shift", "s")
        self.assertEqual([c for c in cb.calls if c[0] == "shot"], [("shot", "full"), ("shot", "region")])

    def test_print_screen_con_ctrl_no_dispara(self):
        e, cb = eng(shot_full={"combo": "print screen", "enabled": True})
        self.assertEqual(press(e, "ctrl", "print screen"), [("ctrl", True), ("print screen", True)])
        self.assertEqual(cb.calls, [])

    def test_desactivada_no_hace_nada(self):
        e, cb = eng(shot_full={"combo": "print screen", "enabled": False})
        self.assertEqual(press(e, "print screen"), [("print screen", True)])

    def test_nombre_en_castellano(self):
        e, cb = eng(shot_full={"combo": "print screen", "enabled": True})
        e.on_event("imprimir pantalla", None, True)
        self.assertEqual(cb.calls, [("shot", "full")])


class Esc(unittest.TestCase):
    def test_esc_solo_mientras_grabas(self):
        e, cb = eng()
        self.assertEqual(press(e, "esc", "^esc"), [("esc", True), ("esc", True)])
        press(e, "windows", "space", "^space", "^windows")
        self.assertEqual(press(e, "esc"), [("esc", False)])
        self.assertIn(("esc", True), cb.calls)


class Captura(unittest.TestCase):
    def run_capture(self, seq, timeout=2.0):
        e, cb = eng()
        res = {}
        t = threading.Thread(target=lambda: res.update(e.capture(timeout)))
        t.start(); time.sleep(0.05)
        out = press(e, *seq)
        t.join()
        return res, out, e

    def test_captura_win_space(self):
        res, out, e = self.run_capture(["windows", "space", "^space", "^windows"])
        self.assertEqual(res, {"combo": "win+space"})
        self.assertTrue(all(v is False for _, v in out))                           # mientras captura, todo se traga

    def test_captura_ctrl_shift_k_orden_canonico(self):
        res, _, _ = self.run_capture(["shift", "ctrl", "k", "^k", "^ctrl", "^shift"])
        self.assertEqual(res, {"combo": "ctrl+shift+k"})

    def test_esc_cancela(self):
        res, _, _ = self.run_capture(["esc"])
        self.assertEqual(res, {"cancel": True})

    def test_solo_modificadores_no_alcanza(self):
        res, _, _ = self.run_capture(["windows", "^windows"], timeout=0.4)
        self.assertEqual(res, {"timeout": True})

    def test_despues_de_capturar_el_teclado_vuelve_a_la_normalidad(self):
        res, out, e = self.run_capture(["windows", "space", "^space", "^windows"])
        self.assertEqual(press(e, "a", "^a"), [("a", True), ("a", True)])


class Config(unittest.TestCase):
    def v(self, **kw):
        cfg = H.default_settings("win+space"); cfg.update(kw)
        return H.validate(cfg)

    def test_default_valido(self):
        self.assertEqual(self.v(), (True, ""))

    def test_duplicado(self):
        ok, msg = self.v(rec=[{"combo": "win+space", "mode": "toggle"}, {"combo": "win+space", "mode": "hold"}])
        self.assertFalse(ok); self.assertIn("misma combinación", msg)

    def test_captura_igual_a_grabacion(self):
        ok, msg = self.v(shot_region={"combo": "win+space", "enabled": True})
        self.assertFalse(ok); self.assertIn("misma combinación", msg)

    def test_tecla_sola_rompe_la_escritura(self):
        ok, msg = self.v(rec=[{"combo": "space", "mode": "toggle"}])
        self.assertFalse(ok); self.assertIn("escritura", msg)

    def test_reservado_de_windows(self):
        ok, msg = self.v(rec=[{"combo": "win+d", "mode": "toggle"}]); self.assertFalse(ok)

    def test_solo_modificador(self):
        ok, msg = self.v(rec=[{"combo": "ctrl+alt", "mode": "toggle"}]); self.assertFalse(ok)

    def test_captura_chocando_con_historial(self):
        ok, msg = self.v(shot_full={"combo": "win+h", "enabled": True}); self.assertFalse(ok); self.assertIn("Historial", msg)

    def test_print_screen_sola_vale(self):
        self.assertTrue(self.v(shot_full={"combo": "print screen", "enabled": True})[0])

    def test_captura_desactivada_no_valida_su_combo(self):
        self.assertTrue(self.v(shot_full={"combo": "basura++", "enabled": False})[0])

    def test_legacy_caps(self):
        c = H.default_settings("caps lock+space")
        self.assertEqual(c["rec"], [{"combo": "caps lock+space", "mode": "hold"}])

    def test_normalizar_limita_a_dos(self):
        c = H.normalize_settings({"rec": [{"combo": "ctrl+alt+1"}, {"combo": "ctrl+alt+2"}, {"combo": "ctrl+alt+3"}]})
        self.assertEqual(len(c["rec"]), 2)

    def test_pretty(self):
        self.assertEqual(H.pretty("win+shift+s"), "Win + Shift + S")
        self.assertEqual(H.pretty("win+space"), "Win + Espacio")


if __name__ == "__main__":
    unittest.main()
