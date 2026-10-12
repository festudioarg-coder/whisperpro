"""Licencias de WhisperPRO: plan Gratis (atajos fijos) o Pro (atajos y capturas a medida).

La licencia es un archivo JSON firmado con Ed25519. La app la verifica SIN conexión y sin ningún servidor:
solo necesita la clave pública (licencia_clave_publica.txt). La clave privada la tiene únicamente FESTUDIOS y
sirve para emitir licencias (ver herramientas/licencias.py). Sin la clave pública cargada, todos son plan Gratis.

Ed25519 está implementado en Python puro (RFC 8032, dominio público) para no sumar dependencias.
"""
import base64
import hashlib
import json
import os
from datetime import date

# ------------------------------------------------------------------ Ed25519 (RFC 8032) ---
_p = 2 ** 255 - 19
_q = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_sqrt_m1 = pow(2, (_p - 1) // 4, _p)


def _inv(x):
    return pow(x, _p - 2, _p)


def _add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _equal(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _recover_x(y, sign):
    if y >= _p:
        return None
    x2 = (y * y - 1) * _inv(_d * y * y + 1)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_p + 3) // 8, _p)
    if (x * x - x2) % _p != 0:
        x = x * _sqrt_m1 % _p
    if (x * x - x2) % _p != 0:
        return None
    if (x & 1) != sign:
        x = _p - x
    return x


_gy = 4 * _inv(5) % _p
_gx = _recover_x(_gy, 0)
_G = (_gx, _gy, 1, _gx * _gy % _p)


def _compress(P):
    zi = _inv(P[2])
    x, y = P[0] * zi % _p, P[1] * zi % _p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % _p)


def _h(s):
    return int.from_bytes(hashlib.sha512(s).digest(), "little") % _q


def _expand(secret):
    h = hashlib.sha512(secret).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def clave_publica(secreta: bytes) -> bytes:
    a, _ = _expand(secreta)
    return _compress(_mul(a, _G))


def firmar(secreta: bytes, mensaje: bytes) -> bytes:
    a, prefix = _expand(secreta)
    A = _compress(_mul(a, _G))
    r = _h(prefix + mensaje)
    Rs = _compress(_mul(r, _G))
    s = (r + _h(Rs + A + mensaje) * a) % _q
    return Rs + int.to_bytes(s, 32, "little")


def firma_valida(publica: bytes, mensaje: bytes, firma: bytes) -> bool:
    if len(publica) != 32 or len(firma) != 64:
        return False
    A = _decompress(publica)
    R = _decompress(firma[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(firma[32:], "little")
    if s >= _q:
        return False
    h = _h(firma[:32] + publica + mensaje)
    return _equal(_mul(s, _G), _add(R, _mul(h, A)))


# ------------------------------------------------------------------ Licencias ---
ARCHIVO_PUBLICA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "licencia_clave_publica.txt")
ARCHIVO_LICENCIA = "licencia.json"


def _publica_hex():
    try:
        with open(ARCHIVO_PUBLICA, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _mensaje(lic: dict) -> bytes:
    """Lo que se firma: la licencia sin la firma, con claves ordenadas, para que sea siempre el mismo texto."""
    cuerpo = {k: v for k, v in lic.items() if k != "firma"}
    return json.dumps(cuerpo, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def emitir(secreta: bytes, email: str, dias=None, hoy=None, plan="pro") -> dict:
    """Crea y firma una licencia. Solo para FESTUDIOS (necesita la clave privada)."""
    hoy = hoy or date.today()
    lic = {"v": 1, "plan": plan, "email": email.strip().lower(), "emitida": hoy.isoformat()}
    if dias:
        lic["vence"] = date.fromordinal(hoy.toordinal() + int(dias)).isoformat()
    lic["firma"] = base64.b64encode(firmar(secreta, _mensaje(lic))).decode("ascii")
    return lic


def verificar(texto, hoy=None, publica_hex=None):
    """Devuelve (True, licencia) o (False, mensaje para mostrarle al usuario)."""
    publica_hex = _publica_hex() if publica_hex is None else publica_hex
    if not publica_hex:
        return False, "Esta versión todavía no puede activar licencias."
    try:
        lic = json.loads(texto) if isinstance(texto, str) else dict(texto)
        publica = bytes.fromhex(publica_hex)
        firma = base64.b64decode(lic.get("firma", ""), validate=True)
    except Exception:
        return False, "La licencia no es válida: pegala completa, tal como te la enviamos."
    if lic.get("v") != 1 or lic.get("plan") != "pro" or not isinstance(lic.get("email"), str):
        return False, "La licencia no es válida para este plan."
    if not firma_valida(publica, _mensaje(lic), firma):
        return False, "La licencia no es válida (la firma no coincide)."
    hoy = hoy or date.today()
    vence = lic.get("vence")
    if vence:
        try:
            if date.fromisoformat(vence) < hoy:
                return False, f"Tu licencia venció el {vence}."
        except ValueError:
            return False, "La licencia no es válida (fecha de vencimiento ilegible)."
    return True, lic


# ------------------------------------------------------------------ Prueba gratis de Pro ---
ARCHIVO_PRUEBA = "prueba.json"
DIAS_PRUEBA = 30
_REG_CLAVE = r"Software\FESTUDIOS\WhisperPRO"


def _reg_leer():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_CLAVE) as k:
            return winreg.QueryValueEx(k, "prueba")[0]
    except Exception:
        return None


def _reg_escribir(valor):
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_CLAVE) as k:
            winreg.SetValueEx(k, "prueba", 0, winreg.REG_SZ, valor)
    except Exception:
        pass


def _inicio_prueba(carpeta):
    """La fecha más antigua entre el archivo y el registro: borrar uno solo no reinicia la prueba."""
    fechas = []
    try:
        with open(os.path.join(carpeta, ARCHIVO_PRUEBA), encoding="utf-8") as f:
            fechas.append(date.fromisoformat(json.load(f)["inicio"]))
    except Exception:
        pass
    try:
        r = _reg_leer()
        if r:
            fechas.append(date.fromisoformat(r))
    except Exception:
        pass
    return min(fechas) if fechas else None


def estado_prueba(carpeta, hoy=None):
    """{'estado': 'nunca'|'activa'|'vencida', 'dias': días que quedan, 'vence': 'AAAA-MM-DD'}"""
    hoy = hoy or date.today()
    ini = _inicio_prueba(carpeta)
    if ini is None:
        return {"estado": "nunca", "dias": DIAS_PRUEBA, "vence": ""}
    vence = date.fromordinal(ini.toordinal() + DIAS_PRUEBA)
    quedan = (vence - hoy).days
    return {"estado": "activa" if quedan >= 0 else "vencida", "dias": max(quedan, 0), "vence": vence.isoformat()}


def iniciar_prueba(carpeta, hoy=None):
    """Arranca la prueba de 30 días (una sola vez por PC). Devuelve (True, estado) o (False, mensaje)."""
    hoy = hoy or date.today()
    est = estado_prueba(carpeta, hoy)
    if est["estado"] != "nunca":
        return False, "La prueba gratis ya se usó en esta PC."
    try:
        with open(os.path.join(carpeta, ARCHIVO_PRUEBA), "w", encoding="utf-8") as f:
            json.dump({"inicio": hoy.isoformat()}, f)
    except OSError:
        return False, "No se pudo iniciar la prueba en esta PC."
    _reg_escribir(hoy.isoformat())
    return True, estado_prueba(carpeta, hoy)


def plan_efectivo(carpeta_datos, congelado=False, entorno=None, hoy=None):
    """('pro'|'gratis', detalle). En modo desarrollo (no instalado) WHISPERPRO_PLAN=pro fuerza Pro para probar."""
    entorno = os.environ if entorno is None else entorno
    if not congelado and entorno.get("WHISPERPRO_PLAN", "").strip().lower() == "pro":
        return "pro", "modo desarrollo"
    try:
        with open(os.path.join(carpeta_datos, ARCHIVO_LICENCIA), encoding="utf-8") as f:
            texto = f.read()
    except OSError:
        texto = None
    if texto is not None:
        ok, res = verificar(texto)
        if ok:
            return "pro", res.get("email", "")
        motivo = res
    else:
        motivo = ""
    if estado_prueba(carpeta_datos, hoy)["estado"] == "activa":
        return "pro", "prueba"
    return "gratis", motivo


def ajustes_para_plan(cfg, plan, defaults):
    """Gratis: los atajos vienen fijos (los de fábrica), sin segundo atajo ni capturas. Pro: los que eligió."""
    return cfg if plan == "pro" else defaults
