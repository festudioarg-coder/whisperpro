"""Pruebas de licencias (sin Windows). Ed25519 se comprueba con los vectores oficiales del RFC 8032."""
import json, os, sys, tempfile, unittest
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import licencia as L
import hotkeys as H

SEC1 = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
PUB1 = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
SIG1 = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
SEC2 = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
PUB2 = "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
SIG2 = "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"


class Ed25519(unittest.TestCase):
    def test_vector_1(self):
        self.assertEqual(L.clave_publica(SEC1).hex(), PUB1)
        self.assertEqual(L.firmar(SEC1, b"").hex(), SIG1)
        self.assertTrue(L.firma_valida(bytes.fromhex(PUB1), b"", bytes.fromhex(SIG1)))

    def test_vector_2(self):
        self.assertEqual(L.clave_publica(SEC2).hex(), PUB2)
        self.assertEqual(L.firmar(SEC2, bytes.fromhex("72")).hex(), SIG2)
        self.assertTrue(L.firma_valida(bytes.fromhex(PUB2), bytes.fromhex("72"), bytes.fromhex(SIG2)))

    def test_mensaje_alterado_no_valida(self):
        self.assertFalse(L.firma_valida(bytes.fromhex(PUB2), bytes.fromhex("73"), bytes.fromhex(SIG2)))

    def test_firma_alterada_no_valida(self):
        malo = bytearray(bytes.fromhex(SIG2)); malo[10] ^= 1
        self.assertFalse(L.firma_valida(bytes.fromhex(PUB2), bytes.fromhex("72"), bytes(malo)))


class Licencias(unittest.TestCase):
    hoy = date(2026, 10, 12)

    def lic(self, **kw):
        return L.emitir(SEC1, kw.pop("email", "Juan@Ejemplo.com"), hoy=self.hoy, **kw)

    def test_emitir_y_verificar(self):
        lic = self.lic(dias=365)
        ok, res = L.verificar(json.dumps(lic), hoy=self.hoy, publica_hex=PUB1)
        self.assertTrue(ok); self.assertEqual(res["email"], "juan@ejemplo.com"); self.assertEqual(res["vence"], "2027-10-12")

    def test_sin_vencimiento(self):
        self.assertTrue(L.verificar(self.lic(), hoy=date(2040, 1, 1), publica_hex=PUB1)[0])

    def test_vencida(self):
        ok, msg = L.verificar(self.lic(dias=10), hoy=date(2026, 11, 1), publica_hex=PUB1)
        self.assertFalse(ok); self.assertIn("venció", msg)

    def test_correo_cambiado_no_valida(self):
        lic = self.lic(); lic["email"] = "otro@ejemplo.com"
        ok, msg = L.verificar(lic, hoy=self.hoy, publica_hex=PUB1)
        self.assertFalse(ok); self.assertIn("firma", msg)

    def test_vencimiento_extendido_no_valida(self):
        lic = self.lic(dias=10); lic["vence"] = "2099-01-01"
        self.assertFalse(L.verificar(lic, hoy=self.hoy, publica_hex=PUB1)[0])

    def test_clave_equivocada(self):
        self.assertFalse(L.verificar(self.lic(), hoy=self.hoy, publica_hex=PUB2)[0])

    def test_sin_clave_publica_nadie_activa(self):
        ok, msg = L.verificar(self.lic(), hoy=self.hoy, publica_hex="")
        self.assertFalse(ok)

    def test_basura(self):
        for t in ("", "hola", "{}", '{"v":1}', "[1,2]"):
            self.assertFalse(L.verificar(t, hoy=self.hoy, publica_hex=PUB1)[0])

    def test_plan_efectivo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(L.plan_efectivo(d, entorno={})[0], "gratis")
            self.assertEqual(L.plan_efectivo(d, congelado=False, entorno={"WHISPERPRO_PLAN": "pro"})[0], "pro")
            # instalada (congelada): la variable de entorno NO regala Pro
            self.assertEqual(L.plan_efectivo(d, congelado=True, entorno={"WHISPERPRO_PLAN": "pro"})[0], "gratis")


class Prueba(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = self._tmp.name
        self._env = {k: os.environ.get(k) for k in ("PROGRAMDATA", "LOCALAPPDATA")}
        os.environ["PROGRAMDATA"] = os.path.join(self.d, "pd")
        os.environ["LOCALAPPDATA"] = os.path.join(self.d, "la")
        self.datos = os.path.join(self.d, "datos")
        os.makedirs(self.datos)
        self._reg = (L._leer_copias, L._escribir_copias)
        self.memreg = []
        orig_l, orig_e = L._leer_copias, L._escribir_copias
        L._leer_copias = lambda c: orig_l(c) + list(self.memreg)
        L._escribir_copias = lambda c, t: (orig_e(c, t), self.memreg.clear(), self.memreg.append(t))
        self._orig = (orig_l, orig_e)

    def tearDown(self):
        L._leer_copias, L._escribir_copias = self._reg
        for k, v in self._env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self._tmp.cleanup()

    def test_prueba_30_dias_una_sola_vez(self):
        h = date(2026, 10, 12)
        self.assertEqual(L.estado_prueba(self.datos, h)["estado"], "nunca")
        self.assertEqual(L.plan_efectivo(self.datos, entorno={}, hoy=h)[0], "gratis")
        ok, est = L.iniciar_prueba(self.datos, h)
        self.assertTrue(ok); self.assertEqual(est["dias"], 30)
        self.assertEqual(L.plan_efectivo(self.datos, entorno={}, hoy=date(2026, 11, 11))[0], "pro")
        self.assertEqual(L.plan_efectivo(self.datos, entorno={}, hoy=date(2026, 11, 12))[0], "gratis")
        self.assertFalse(L.iniciar_prueba(self.datos, date(2026, 12, 1))[0])

    def test_borrar_una_copia_no_reinicia(self):
        L.iniciar_prueba(self.datos, date(2026, 10, 12))
        os.remove(os.path.join(self.datos, "prueba.json"))
        self.assertEqual(L.estado_prueba(self.datos, date(2026, 10, 20))["dias"], 22)
        self.assertTrue(os.path.exists(os.path.join(self.datos, "prueba.json")))   # se repara sola

    def test_editar_la_fecha_invalida_la_prueba(self):
        L.iniciar_prueba(self.datos, date(2026, 10, 12))
        ruta = os.path.join(self.datos, "prueba.json")
        r = json.load(open(ruta)); r["inicio"] = "2026-12-01"
        json.dump(r, open(ruta, "w"))
        self.assertEqual(L.estado_prueba(self.datos, date(2026, 10, 13))["estado"], "vencida")

    def test_copiar_el_registro_de_otra_pc_no_sirve(self):
        L.iniciar_prueba(self.datos, date(2026, 10, 12))
        ruta = os.path.join(self.datos, "prueba.json")
        r = json.load(open(ruta)); r["mid"] = "otra-pc"
        json.dump(r, open(ruta, "w"))
        self.assertEqual(L.estado_prueba(self.datos, date(2026, 10, 13))["estado"], "vencida")

    def test_atrasar_el_reloj_no_estira_la_prueba(self):
        L.iniciar_prueba(self.datos, date(2026, 10, 12))
        L.estado_prueba(self.datos, date(2026, 11, 5))                       # se ve el 5/11
        self.assertEqual(L.estado_prueba(self.datos, date(2026, 10, 20))["estado"], "vencida")


class Gating(unittest.TestCase):
    def test_gratis_fuerza_los_atajos_de_fabrica(self):
        defaults = H.default_settings("win+space")
        elegido = {"rec": [{"combo": "ctrl+alt+d", "mode": "hold"}, {"combo": "ctrl+alt+e", "mode": "toggle"}],
                   "shot_region": {"combo": "win+shift+s", "enabled": True}, "shot_full": {"combo": "print screen", "enabled": True}, "shot_save": True}
        r = L.ajustes_para_plan(elegido, "gratis", defaults)
        self.assertEqual(r["rec"], [{"combo": "win+space", "mode": "toggle"}])
        self.assertFalse(r["shot_region"]["enabled"]); self.assertFalse(r["shot_full"]["enabled"])

    def test_pro_respeta_lo_elegido(self):
        elegido = {"rec": [{"combo": "ctrl+alt+d", "mode": "hold"}]}
        self.assertIs(L.ajustes_para_plan(elegido, "pro", H.default_settings()), elegido)


if __name__ == "__main__":
    unittest.main()
