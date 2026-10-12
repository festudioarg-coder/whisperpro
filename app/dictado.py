"""
Dictado — push-to-talk con transcripción en vivo, autocorrección inteligente e historial.

Mantené Bloq Mayús + Espacio: grabás y el texto va apareciendo en el input a medida que hablás.
Soltá: la IA interpreta tus correcciones ("no, mejor no, borrá eso") y deja la versión final.
Bloq Mayús + H: historial (mensaje completo, lo descartado, copiar).
"""
import os
import io
import sys
import json
import time
import wave
import threading
import tempfile
from datetime import datetime

import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
from dotenv import load_dotenv

FROZEN = getattr(sys, "frozen", False)
RES = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))   # recursos (ui/, .env.example)
if FROZEN:
    BASE = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "WhisperPRO")  # datos del usuario
    os.makedirs(BASE, exist_ok=True)
    if not os.path.exists(os.path.join(BASE, ".env")) and os.path.exists(os.path.join(RES, ".env.example")):
        import shutil
        shutil.copy(os.path.join(RES, ".env.example"), os.path.join(BASE, ".env"))
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE, ".env")
load_dotenv(ENV_PATH)

VERSION = "v6.14"
DEBUG = os.getenv("DICTADO_DEBUG", "0") == "1"
HOTKEY = os.getenv("DICTADO_HOTKEY", "win+space")
HISTORY_KEY = os.getenv("DICTADO_HISTORY_KEY", "h")
LANG = os.getenv("DICTADO_LANG", "").strip()
LIVE = os.getenv("DICTADO_LIVE", "1") == "1"            # escribir en vivo mientras hablás
LIVE_INTERVAL = float(os.getenv("DICTADO_LIVE_INTERVAL", "1.5"))
SMART = os.getenv("DICTADO_SMART", "1") == "1"          # autocorrección con LLM
SAMPLE_RATE = 16000
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_KEY = (os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")).strip()
LOCAL_MODEL = os.getenv("DICTADO_LOCAL_MODEL", "small")
HISTORY_FILE = os.path.join(BASE, "historial.jsonl")
CLIP_FILE = os.path.join(BASE, "portapapeles.jsonl")
KEEP_CLIP = os.getenv("DICTADO_CLIPBOARD", "1") == "1"   # dejar el dictado en el portapapeles al terminar
LANG_NAMES = {"es": "español", "en": "inglés", "pt": "portugués"}


LOG_FILE = os.path.join(BASE, "dictado.log")


class _Tee:
    """Todo lo que se imprime va también a dictado.log (para poder diagnosticar sin consola)."""

    def __init__(self, stream):
        self.stream = stream
        try:
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 2_000_000:
                os.replace(LOG_FILE, LOG_FILE + ".old")
        except Exception:
            pass
        self.f = open(LOG_FILE, "a", encoding="utf-8", errors="replace")

    def write(self, data):
        try:
            if self.stream:
                self.stream.write(data)
        except Exception:
            pass
        try:
            self.f.write(data)
            self.f.flush()
        except Exception:
            pass

    def flush(self):
        try:
            if self.stream:
                self.stream.flush()
        except Exception:
            pass


def _thread_hook(args):
    import traceback
    print(f"[dictado] ERROR en hilo {getattr(args.thread, 'name', '?')}:", flush=True)
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)


threading.excepthook = _thread_hook
sys.stdout = _Tee(sys.stdout)
sys.stderr = _Tee(sys.stderr)
print(f"\n===== {datetime.now().isoformat(timespec='seconds')} arranque =====", flush=True)


def log(msg):
    print(f"[dictado] {msg}", flush=True)


def dbg(msg):
    if DEBUG:
        print(f"[debug] {msg}", flush=True)


# =====================================================================
# Motores de transcripción (STT) y de corrección (LLM)
# =====================================================================
_groq_client = None
_openai_client = None
_gemini_client = None
_local_model = None


def _groq():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_KEY)
    return _groq_client


def _openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_KEY)
    return _openai_client


def _gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_KEY)
    return _gemini_client


_stt_ctx = {"prompt": ""}


def stt_groq(wav: bytes) -> str:
    for model in groq_models("stt"):
        kw = dict(file=("a.wav", wav), model=model, response_format="text", temperature=0)
        if LANG:
            kw["language"] = LANG
        if _stt_ctx["prompt"]:
            kw["prompt"] = _stt_ctx["prompt"][-220:]   # contexto: mantiene idioma y continuidad entre tramos
        try:
            return str(_groq().audio.transcriptions.create(**kw)).strip()
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                log("Groq: límite de uso por minuto alcanzado; espero 3 s y reintento")
                time.sleep(3)
                return str(_groq().audio.transcriptions.create(**kw)).strip()
            if _is_model_gone(e):
                log(f"Groq STT: {model} ya no existe, actualizo lista")
                groq_models("stt", refresh=True)
                continue
            raise
    raise RuntimeError("Groq no tiene ningún modelo Whisper disponible")


def stt_openai(wav: bytes) -> str:
    kw = dict(file=("a.wav", wav), model="whisper-1", response_format="text", temperature=0)
    if LANG:
        kw["language"] = LANG
    return str(_openai().audio.transcriptions.create(**kw)).strip()


def stt_gemini(wav: bytes) -> str:
    from google.genai import types
    idioma = f" El audio está en {LANG_NAMES.get(LANG, LANG)}." if LANG else " Puede estar en español, inglés o portugués."
    prompt = ("Transcribí exactamente lo que dice el audio, con puntuación y acentos." + idioma +
              " Devolvé solo el texto, sin comillas ni comentarios. Si no hay voz, devolvé vacío.")
    r = _gemini().models.generate_content(
        model=os.getenv("DICTADO_GEMINI_MODEL", "gemini-2.5-flash"),
        contents=[types.Part.from_bytes(data=wav, mime_type="audio/wav"), prompt],
        config=types.GenerateContentConfig(temperature=0))
    return (r.text or "").strip()


def stt_local(wav: bytes) -> str:
    global _local_model
    try:
        from faster_whisper import WhisperModel
    except Exception:
        raise RuntimeError("Falta configurar una API key (abrí Configuración en el ícono de la bandeja)")
    if _local_model is None:
        log(f"cargando modelo local '{LOCAL_MODEL}'...")
        _local_model = WhisperModel(LOCAL_MODEL, device="auto", compute_type="int8")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav)
        path = f.name
    try:
        segs, _ = _local_model.transcribe(path, language=LANG or None, beam_size=5)
        return " ".join(s.text.strip() for s in segs).strip()
    finally:
        os.remove(path)


STT = [("Groq", GROQ_KEY, stt_groq), ("OpenAI", OPENAI_KEY, stt_openai), ("Gemini", GEMINI_KEY, stt_gemini)]


# ---------- clave de IA: conexión guiada (sin editar archivos) ----------
import re as _re
GROQ_KEYS_URL = "https://console.groq.com/keys"
_KEY_RE = _re.compile(r"gsk_[A-Za-z0-9]{20,}")
_key_flow = {"tried": "", "msg": ""}


def has_any_key():
    return any(k for _, k, _ in STT)


def mask_key(k):
    return (k[:4] + "…" + k[-4:]) if k and len(k) > 10 else ""


def validate_groq_key(key):
    """True si Groq acepta la clave (pide la lista de modelos)."""
    try:
        from groq import Groq
        Groq(api_key=key, timeout=8.0, max_retries=0).models.list()
        return True, ""
    except Exception as e:
        t = str(e)
        if "401" in t or "invalid" in t.lower():
            return False, "Groq dice que esa clave no es válida"
        return False, "No pude comprobarla (¿hay internet?)"


def apply_groq_key(key):
    """Guarda la clave en el .env del usuario y la activa sin reiniciar."""
    global GROQ_KEY, _groq_client
    key = key.strip()
    lines = []
    try:
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = [l.rstrip("\r\n") for l in f if not l.strip().startswith("GROQ_API_KEY")]
    except FileNotFoundError:
        pass
    lines.append(f"GROQ_API_KEY={key}")
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.environ["GROQ_API_KEY"] = key
    GROQ_KEY, _groq_client = key, None
    STT[0] = ("Groq", key, stt_groq)
    log(f"clave de Groq conectada ({mask_key(key)})")
    threading.Thread(target=lambda: (groq_models("llm", refresh=True), groq_models("stt")), daemon=True).start()


def transcribe(wav: bytes) -> str:
    for name, key, fn in STT:
        if not key:
            continue
        try:
            return fn(wav)
        except Exception as e:
            log(f"{name} STT falló ({e}); probando siguiente...")
    return stt_local(wav)


SMART_PROMPT = """Sos un editor de dictado por voz. Recibís la transcripción literal de lo que una persona dijo en voz alta mientras dictaba un mensaje.
Tu trabajo: devolver el mensaje FINAL que la persona quiso escribir, aplicando sus propias correcciones habladas.

Reglas:
- Si se corrige hablando, en cualquier variante del español ("no, mejor no", "borrá eso" / "borra eso" / "bórralo", "olvidate de eso" / "olvídalo", "quita eso", "eso no", "no, espera", "en realidad", "digo", "perdón" / "perdona", "mejor dicho", "en vez de X, Y") o en inglés ("scratch that", "I mean", "actually"): eliminá lo que pidió descartar y quedate con la versión corregida.
- Sacá muletillas (eh, em, este, o sea, pues, bueno, tipo, like, um) y repeticiones de dictado, pero NO cambies el estilo ni el tono: mantené las palabras de la persona.
- Respetá la variante regional tal cual: si usa vos/tenés, tú/tienes, usted o vosotros, mantenela; no cambies vocabulario local (auto/carro/coche, celular/móvil, computadora/ordenador). Nunca "neutralices" ni traduzcas.
- No agregues contenido nuevo, no resumas, no expliques. Corregí puntuación y mayúsculas.
- Mantené el idioma original.
- Si no hay correcciones, devolvé el texto casi igual, solo limpio.

Respondé SOLO con JSON válido: {"final": "<mensaje final>", "descartado": ["<fragmento descartado 1>", ...]}
"""


def _parse_json(s: str):
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    a, b = s.find("{"), s.rfind("}")
    return json.loads(s[a:b + 1])


# ---------- descubrimiento automático de modelos de Groq ----------
# Groq da de baja modelos seguido. En vez de nombres fijos: consultamos /models, elegimos por preferencia,
# guardamos en caché (modelos.json) y refrescamos cada 12 h o apenas uno falla con "model_not_found".
MODELS_CACHE = os.path.join(BASE, "modelos.json")
LLM_PREF = ["gpt-oss-120b", "llama-3.3-70b", "kimi-k2", "qwen3-32b", "llama-4-maverick", "llama-4-scout",
            "gpt-oss-20b", "deepseek", "llama-3.1-70b", "mixtral", "llama-3.1-8b", "gemma2", "llama3"]
STT_PREF = ["whisper-large-v3", "whisper-large-v3-turbo", "distil-whisper"]   # v3 completo: menos errores en español, mismo cupo gratis
LLM_EXCLUDE = ("whisper", "tts", "guard", "orpheus", "playai", "embed", "vision", "safeguard", "compound", "allam")
_models_mem = {"at": 0.0, "llm": [], "stt": []}


def _is_model_gone(e) -> bool:
    m = str(e).lower()
    return any(k in m for k in ("model_not_found", "does not exist", "decommissioned", "deprecated", "not supported", "no longer"))


def _rank(ids, pref):
    def key(mid):
        low = mid.lower()
        for i, p in enumerate(pref):
            if p in low:
                return (i, len(low))
        return (len(pref), len(low))
    return sorted(ids, key=key)


def groq_models(kind="llm", refresh=False):
    """Lista ordenada de modelos vigentes en Groq para 'llm' o 'stt'. Con caché en disco y en memoria."""
    now = time.time()
    if not refresh and _models_mem["at"] and now - _models_mem["at"] < 12 * 3600 and _models_mem[kind]:
        return _models_mem[kind]
    if not refresh and not _models_mem["at"]:
        try:
            with open(MODELS_CACHE, encoding="utf-8") as f:
                c = json.load(f)
            if now - c.get("at", 0) < 12 * 3600 and c.get("llm") and c.get("stt"):
                c["stt"] = _rank(c["stt"], STT_PREF)      # si cambia la preferencia, la caché la respeta
                _models_mem.update(c)
                return _models_mem[kind]
        except Exception:
            pass
    try:
        data = _groq().models.list().data
        ids = [m.id for m in data if getattr(m, "active", True)] or [m.id for m in data]
        llm = _rank([i for i in ids if not any(x in i.lower() for x in LLM_EXCLUDE)], LLM_PREF)
        stt = _rank([i for i in ids if "whisper" in i.lower()], STT_PREF)
        forced = os.getenv("DICTADO_LLM", "").strip()
        if forced:
            llm = [forced] + [m for m in llm if m != forced]
        _models_mem.update({"at": now, "llm": llm, "stt": stt})
        try:
            with open(MODELS_CACHE, "w", encoding="utf-8") as f:
                json.dump(_models_mem, f, ensure_ascii=False, indent=1)
        except Exception:
            pass
        log(f"modelos Groq actualizados: corrección={llm[:3]} … stt={stt[:2]}")
    except Exception as e:
        log(f"no pude listar modelos de Groq ({e}); uso lista de respaldo")
        if not _models_mem["llm"]:
            _models_mem["llm"] = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
        if not _models_mem["stt"]:
            _models_mem["stt"] = ["whisper-large-v3-turbo", "whisper-large-v3"]
        _models_mem["at"] = now - 11 * 3600   # reintentar pronto
    return _models_mem[kind]


_groq_llm_ok = {"model": None}


def _groq_chat_json(raw: str):
    """Prueba los modelos de Groq en orden y se queda con el primero que responde (cambian seguido)."""
    models = groq_models("llm")
    order = ([_groq_llm_ok["model"]] if _groq_llm_ok["model"] else []) + [m for m in models if m != _groq_llm_ok["model"]]
    last_err = None
    for model in order:
        try:
            kw = dict(model=model, temperature=0,
                      messages=[{"role": "system", "content": SMART_PROMPT}, {"role": "user", "content": raw}],
                      response_format={"type": "json_object"})
            if "gpt-oss" in model:
                kw["reasoning_effort"] = "low"      # mucho más rápido; la tarea es simple
            elif "qwen3" in model:
                kw["reasoning_effort"] = "none"
            try:
                r = _groq().chat.completions.create(**kw)
            except TypeError:
                kw.pop("reasoning_effort", None)
                r = _groq().chat.completions.create(**kw)
            d = _parse_json(r.choices[0].message.content)
            if _groq_llm_ok["model"] != model:
                _groq_llm_ok["model"] = model
                log(f"corrección: usando {model}")
            return d
        except Exception as e:
            last_err = e
            if _is_model_gone(e):
                if _groq_llm_ok["model"] == model:
                    _groq_llm_ok["model"] = None
                groq_models("llm", refresh=True)
                continue
            if "json" in str(e).lower() and "response_format" in str(e).lower():
                continue   # ese modelo no soporta JSON: probar el siguiente
            raise
    raise RuntimeError(f"ningún modelo de Groq disponible ({last_err})")


def smart_edit(raw: str):
    """Devuelve (final, descartado[]) interpretando las autocorrecciones del dictado."""
    if not SMART or len(raw.split()) < 3:
        return raw, []
    try:
        d = None
        if GROQ_KEY:
            try:
                d = _groq_chat_json(raw)
            except Exception as e:
                log(f"corrección en Groq falló ({e}); pruebo otro proveedor")
        if d is not None:
            pass
        elif OPENAI_KEY:
            r = _openai().chat.completions.create(
                model=os.getenv("DICTADO_LLM", "gpt-4o-mini"), temperature=0,
                messages=[{"role": "system", "content": SMART_PROMPT},
                          {"role": "user", "content": raw}],
                response_format={"type": "json_object"})
            d = _parse_json(r.choices[0].message.content)
        elif GEMINI_KEY:
            from google.genai import types
            r = _gemini().models.generate_content(
                model=os.getenv("DICTADO_GEMINI_MODEL", "gemini-2.5-flash"),
                contents=[SMART_PROMPT + "\n\nTranscripción:\n" + raw],
                config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
            d = _parse_json(r.text or "")
        else:
            return raw, []
        final = (d.get("final") or "").strip()
        desc = [x for x in (d.get("descartado") or []) if isinstance(x, str) and x.strip()]
        return (final or raw), desc
    except Exception as e:
        log(f"autocorrección falló ({e}); uso el texto literal")
        return raw, []


# =====================================================================
# Historial
# =====================================================================
def save_history(raw: str, final: str, discarded, seconds: float):
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "raw": raw, "final": final,
           "descartado": discarded, "segundos": round(seconds, 1)}
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        log(f"no pude guardar historial: {e}")


def load_history(n=200):
    out = []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return out[-n:]


def save_clip(text: str, origen: str):
    """Guarda en el portapapeles interno lo que había antes de pisar el clipboard (o un dictado)."""
    text = (text or "").strip()
    if not text or len(text) > 20000:
        return
    try:
        last = load_clips(1)
        if last and last[-1]["texto"] == text:
            return
        with open(CLIP_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "origen": origen,
                                "texto": text}, ensure_ascii=False) + "\n")
    except Exception as e:
        log(f"no pude guardar portapapeles: {e}")


def load_clips(n=100):
    out = []
    try:
        with open(CLIP_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return out[-n:]


# =====================================================================
# Estado compartido con la UI
# =====================================================================
UI = {"state": "idle", "level": 0.0, "live": "", "text": "", "since": 0.0, "t0": 0.0,
      "open_history": False, "open_setup": False, "discarded": 0, "elapsed": 0.0}
_last = {"final": "", "raw": ""}   # último dictado pegado (para deshacer)


def set_state(state, text=""):
    UI["state"] = state
    UI["text"] = text
    UI["since"] = time.time()


# =====================================================================
# Escritura en la app destino
# =====================================================================
_typing_lock = threading.Lock()
_typed = ""          # lo que ya escribimos en vivo en el input
_injecting = False   # True mientras mandamos teclas nosotros (el hook las deja pasar)


def _write(text: str):
    global _injecting
    if not text:
        return
    _injecting = True
    try:
        keyboard.write(text, delay=0)
    finally:
        _injecting = False


def _backspace(n: int):
    global _injecting
    if n <= 0:
        return
    _injecting = True
    try:
        for _ in range(n):
            keyboard.send("backspace")
    finally:
        _injecting = False


def _paste(text: str):
    global _injecting
    try:
        prev = pyperclip.paste()
    except Exception:
        prev = None
    if prev and prev.strip() != text.strip():
        save_clip(prev, "anterior")   # lo que había antes queda recuperable en Bloq Mayús + H
    pyperclip.copy(text)
    time.sleep(0.04)
    _injecting = True
    try:
        keyboard.send("ctrl+v")
    finally:
        _injecting = False
    time.sleep(0.12)
    if KEEP_CLIP:
        save_clip(text, "dictado")    # el dictado queda en el portapapeles del sistema
    elif prev is not None:
        try:
            pyperclip.copy(prev)
        except Exception:
            pass


def live_update(text: str):
    """Actualiza lo escrito en el input para que coincida con `text` (agrega o corrige)."""
    global _typed
    with _typing_lock:
        if text == _typed:
            return
        i = 0
        m = min(len(text), len(_typed))
        while i < m and text[i] == _typed[i]:
            i += 1
        _backspace(len(_typed) - i)
        _write(text[i:])
        _typed = text


def finalize_text(final: str):
    global _typed
    with _typing_lock:
        _backspace(len(_typed))
        _typed = ""
        if final:
            _paste(final + " ")


def undo_last():
    """Bloq Mayús + Z: reemplaza el último dictado pegado por lo que dijiste literal (y viceversa)."""
    if not _last["final"]:
        return
    with _typing_lock:
        _backspace(len(_last["final"]) + 1)
        _last["final"], _last["raw"] = _last["raw"], _last["final"]
        _paste(_last["final"] + " ")
    UI["discarded"] = 0
    set_state("done", _last["final"])
    log("deshacer: " + _last["final"])


# =====================================================================
# Grabación + transcripción en vivo
# =====================================================================
_frames = []
_stream = None
_recording = False
_rec_lock = threading.Lock()
_session = 0  # id de la grabación actual (para descartar resultados viejos)


def _audio_cb(indata, frames, t, status):
    if _recording:
        _frames.append(indata.copy())
        rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2))) / 32768.0
        lvl = min(1.0, (rms * 14) ** 0.6)
        UI["level"] = max(lvl, UI["level"] * 0.6)
        with _levels_lock:
            _levels.append(round(lvl, 3))
            if len(_levels) > 60:
                del _levels[:-60]


def _wav_bytes(frames):
    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(audio.tobytes())
    return buf.getvalue(), len(audio) / SAMPLE_RATE


# ---------- transcripción por tramos (corta en las pausas) ----------
# Cada tramo se transcribe UNA vez. Al terminar solo falta el último tramo: más rápido y ~20x menos
# consumo del cupo de Groq que reenviar todo el audio cada vez.
_seg = {"committed": 0, "text": [], "lock": threading.Lock(), "busy": False}
_rate = {"times": []}
RATE_MAX = int(os.getenv("DICTADO_RPM", "18"))   # plan gratis de Groq: 20 transcripciones/minuto


def _rate_ok():
    now = time.time()
    _rate["times"] = [t for t in _rate["times"] if now - t < 60]
    return len(_rate["times"]) < RATE_MAX


def _rate_mark():
    _rate["times"].append(time.time())


def _block_rms(f):
    return float(np.sqrt(np.mean(f.astype(np.float32) ** 2))) / 32768.0


HALLUCINATIONS = ("thank you", "thanks for watching", "gracias por ver", "subtítulos realizados", "amara.org",
                  "suscríbete", "suscribete", "gracias.", "you", "bye", "¡gracias!", "música", "[música]", "...")


def _speech_seconds(frames, i0, i1):
    """Segundos con voz en el tramo (bloques por encima del piso de ruido)."""
    if i1 <= i0:
        return 0.0
    rms = [_block_rms(f) for f in frames[i0:i1]]
    if not rms:
        return 0.0
    # piso de ruido medido en TODA la grabación (no solo en el tramo), y umbral con techo:
    # si hablás de corrido el "piso" sube, pero el techo de 0,03 impide que tu voz cuente como ruido.
    allr = [_block_rms(f) for f in frames[: max(i1, 1): 3]]
    floor = float(np.percentile(allr, 10)) if allr else 0.0
    # mínimo bajo (0,0025): con micrófonos de nivel bajo la voz ronda 0,004-0,008 y antes quedaba toda como "silencio"
    thr = min(max(0.0025, floor * 2.5), 0.011)
    return sum(1 for r in rms if r > thr) * 480 / SAMPLE_RATE


def _clean_hallucination(txt: str) -> str:
    t = txt.strip()
    low = t.lower().strip(" .!¡?¿")
    if not low:
        return ""
    # frase fantasma sola o repetida ("Thank you. Thank you. …")
    parts = [p.strip(" .!¡?¿").lower() for p in t.replace("!", ".").split(".") if p.strip(" .!¡?¿")]
    if parts and all(any(p == h.strip(" .!¡?¿") for h in HALLUCINATIONS) for p in parts):
        return ""
    return t


def _transcribe_range(frames, i0, i1):
    if i1 - i0 <= 0:
        return ""
    if _speech_seconds(frames, i0, i1) < 0.3:
        return ""                     # sin voz: no se manda (Whisper inventa "Thank you" con silencio)
    wav, secs = _wav_bytes(frames[i0:i1])
    if secs < 0.35:
        return ""
    _rate_mark()
    txt = _clean_hallucination(transcribe(wav))
    if txt:
        _stt_ctx["prompt"] = (_stt_ctx["prompt"] + " " + txt).strip()
    return txt


def _live_loop(session):
    """Mira el audio cada 150 ms; cuando hay una pausa (o el tramo pasa 12 s), transcribe ese tramo y lo suma."""
    BLOCK_S = 480 / SAMPLE_RATE
    PAUSE_BLOCKS = int(0.55 / BLOCK_S)       # ~0,55 s de silencio = fin de frase
    MIN_SEG_BLOCKS = int(1.2 / BLOCK_S)
    MAX_SEG_BLOCKS = int(12 / BLOCK_S)
    while _recording and session == _session:
        time.sleep(0.15)
        frames = _frames
        n = len(frames)
        with _seg["lock"]:
            c0 = _seg["committed"]
        pending = n - c0
        if pending < MIN_SEG_BLOCKS or _seg["busy"] or not _rate_ok():
            continue
        tail = frames[max(c0, n - PAUSE_BLOCKS):n]
        rms_tail = max((_block_rms(f) for f in tail), default=0)
        noise = np.percentile([_block_rms(f) for f in frames[max(0, n - 300):n:3]] or [0.0], 15)
        silent = rms_tail < max(0.0025, noise * 2.2)
        if not (silent or pending >= MAX_SEG_BLOCKS):
            continue
        _seg["busy"] = True
        try:
            txt = _transcribe_range(frames, c0, n)
        except Exception as e:
            dbg(f"tramo: {e}")
            txt = None
        finally:
            _seg["busy"] = False
        if session != _session:
            break
        if txt is None:
            continue
        with _seg["lock"]:
            if _seg["committed"] == c0:
                _seg["committed"] = n
                if txt:
                    _seg["text"].append(txt)
                live = " ".join(_seg["text"])
        if txt:
            UI["live"] = live
            if LIVE and _recording:
                live_update(live)


def start_recording():
    global _stream, _recording, _frames, _session
    if UI.get("paused"):
        return
    if not has_any_key():
        UI["open_setup"] = True
        return
    with _rec_lock:
        if _recording:
            return
        _frames = []
        UI["live"] = ""
        with _seg["lock"]:
            _seg["committed"], _seg["text"] = 0, []
        _stt_ctx["prompt"] = "Dictado en español, con puntuación." if not LANG or LANG == "es" else ""
        try:
            _stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=480, callback=_audio_cb)
            _stream.start()
        except Exception as e:
            log(f"ERROR abriendo micrófono: {e}")
            set_state("error", "Sin micrófono")
            _stream = None
            return
        _recording = True
        _session += 1
        UI["t0"] = time.time()
        set_state("listening")
        log("grabando...")
        threading.Thread(target=_live_loop, args=(_session,), daemon=True).start()


def cancel_recording():
    """Esc dos veces: descarta todo lo grabado y borra lo que se escribió en vivo."""
    global _stream, _recording, _session
    with _rec_lock:
        if not _recording:
            return
        _recording = False
        _session += 1          # invalida el hilo de tramos en curso
        try:
            _stream.stop()
            _stream.close()
        except Exception:
            pass
        _stream = None
    _confirm["at"] = 0.0
    finalize_text("")          # borra el texto que ya se había escrito en vivo
    UI["live"] = ""
    log("grabación descartada con Esc")
    set_state("error", "Grabación descartada")


def stop_recording():
    global _stream, _recording
    with _rec_lock:
        if not _recording:
            return
        _recording = False
        try:
            _stream.stop()
            _stream.close()
        except Exception:
            pass
        _stream = None
        frames = list(_frames)
    secs = sum(len(f) for f in frames) / SAMPLE_RATE
    if not frames or secs < 0.4:
        log("audio muy corto, ignorado")
        if _typed:
            finalize_text("")
        set_state("idle")
        return
    set_state("thinking")
    threading.Thread(target=_finish, args=(frames, secs), daemon=True).start()


def _finish(frames, secs):
    t0 = time.time()
    # esperar si justo se está transcribiendo un tramo
    for _ in range(100):
        if not _seg["busy"]:
            break
        time.sleep(0.03)
    with _seg["lock"]:
        c0, parts = _seg["committed"], list(_seg["text"])
    try:
        tail = _transcribe_range(frames, c0, len(frames))
    except Exception as e:
        log(f"error transcribiendo el final ({e}); reintento con todo el audio")
        try:
            wav, _ = _wav_bytes(frames)
            parts, tail = [], transcribe(wav)
        except Exception as e2:
            log(f"error transcribiendo: {e2}")
            set_state("error", "No se pudo transcribir")
            return
    try:
        _r = [_block_rms(f) for f in frames[::3]]
        dbg(f"niveles mic: piso {np.percentile(_r, 10):.4f} | medio {np.percentile(_r, 50):.4f} | voz {np.percentile(_r, 90):.4f} | tramos con texto en vivo: {len(parts)}")
    except Exception:
        pass
    raw = " ".join(p for p in parts + [tail] if p).strip()
    if not raw and secs >= 0.8:
        # red de seguridad: si el detector no vio voz, se manda todo igual (el filtro saca frases fantasma)
        try:
            wav, _ = _wav_bytes(frames)
            _rate_mark()
            raw = _clean_hallucination(transcribe(wav))
        except Exception as e:
            log(f"error transcribiendo: {e}")
    if not raw:
        log(f"no se reconoció voz ({secs:.1f}s de audio, {_speech_seconds(frames, 0, len(frames)):.1f}s con voz detectada)")
        finalize_text("")
        set_state("error", "No escuché nada")
        return
    t_stt = time.time() - t0
    final, discarded = smart_edit(raw)
    log(f"{time.time() - t0:.1f}s (transcripción {t_stt:.1f}s + corrección {time.time() - t0 - t_stt:.1f}s, {len(parts) + 1} tramos, {secs:.0f}s de audio) | literal: {raw}")
    if discarded:
        log(f"descartado: {discarded}")
    log(f"final: {final}")
    save_history(raw, final, discarded, secs)
    UI["discarded"] = len(discarded)
    UI["elapsed"] = time.time() - t0
    _last["final"], _last["raw"] = final, raw
    set_state("done", final)
    finalize_text(final)


# =====================================================================
# Atajos de teclado
# =====================================================================
CAPS_SC, SPACE_SC = 58, 57


WIN_SCS = (91, 92)


def _setup_win_mode(second_key: str):
    """Win + Espacio: empieza a grabar (podés soltar). Espacio solo: corta. Win+H historial, Win+Z deshacer."""
    st = {"win": False, "used": False}
    cnt = [0]

    def is_win(e):
        return e.scan_code in WIN_SCS or (e.name or "").lower() in ("left windows", "right windows", "windows", "win")

    def is_second(e):
        if second_key == "space":
            return e.scan_code == SPACE_SC or (e.name or "").lower() in ("space", "espacio")
        return (e.name or "").lower() == second_key

    def eat_win():
        # Windows abre el menú Inicio si soltás Win sin otra tecla "vista"; le mandamos un Ctrl para que no lo haga
        global _injecting
        _injecting = True
        try:
            keyboard.send("ctrl")
        finally:
            _injecting = False

    def hook(e):
        if _injecting:
            return True
        if DEBUG and cnt[0] < 40:
            cnt[0] += 1
            print(f"[key] {e.event_type:<4} name={e.name!r} sc={e.scan_code}", flush=True)
        name = (e.name or "").lower()
        if is_win(e):
            st["win"] = e.event_type == "down"
            if not st["win"]:
                st["used"] = False
            return True
        if e.scan_code == 1 or name in ("esc", "escape"):
            if _recording:
                if e.event_type == "down":
                    if confirm_active():
                        threading.Thread(target=cancel_recording, daemon=True).start()
                    else:
                        _confirm["at"] = time.time()
                return False                  # el Esc no le llega a la app mientras grabás
            return True
        if is_second(e):
            if e.event_type == "down":
                if _recording:
                    _confirm["at"] = 0.0
                    stop_recording()          # Espacio solo corta la grabación
                    return False
                if st["win"] and not st["used"]:
                    st["used"] = True
                    eat_win()
                    start_recording()
                    return False
            elif _recording or st["used"]:
                return False                  # no dejar pasar la suelta del espacio que usamos
            return True
        if st["win"] and e.event_type == "down":
            if name == HISTORY_KEY.lower():
                st["used"] = True
                eat_win()
                UI["open_history"] = True
                return False
            if name == "z":
                st["used"] = True
                eat_win()
                threading.Thread(target=undo_last, daemon=True).start()
                return False
        return True

    keyboard.hook(hook, suppress=True)
    log(f"atajo: Win + {second_key} empieza (soltá las teclas) · {second_key} corta · historial: Win + {HISTORY_KEY} · deshacer: Win + Z")


def setup_hotkeys():
    parts = [p.strip().lower() for p in HOTKEY.split("+")]
    if parts[0] in ("win", "windows", "cmd", "super"):
        _setup_win_mode(parts[-1] if len(parts) > 1 else "space")
        return
    if parts[0] not in ("caps lock", "capslock", "bloq mayus", "bloq mayús"):
        keyboard.add_hotkey(HOTKEY, start_recording, trigger_on_release=False)
        keyboard.on_release_key(parts[-1], lambda e: stop_recording())
        keyboard.add_hotkey(f"ctrl+alt+{HISTORY_KEY}", lambda: UI.__setitem__("open_history", True))
        log(f"atajo: {HOTKEY} (mantener) | historial: ctrl+alt+{HISTORY_KEY}")
        return

    second = parts[-1] if len(parts) > 1 else "space"
    st = {"caps": False, "used": False, "passthrough": False}
    cnt = [0]

    def is_caps(e):
        return e.scan_code == CAPS_SC or (e.name or "").lower() in ("caps lock", "bloq mayús", "bloq mayus")

    def is_second(e):
        if second == "space":
            return e.scan_code == SPACE_SC or (e.name or "").lower() in ("space", "espacio")
        return (e.name or "").lower() == second

    def is_hist(e):
        return (e.name or "").lower() == HISTORY_KEY.lower()

    def is_undo(e):
        return (e.name or "").lower() == "z"

    def hook(e):
        if _injecting:
            return True
        if DEBUG and cnt[0] < 40:
            cnt[0] += 1
            print(f"[key] {e.event_type:<4} name={e.name!r} sc={e.scan_code}", flush=True)
        if is_caps(e):
            if st["passthrough"]:
                return True
            if e.event_type == "down":
                if not st["caps"]:
                    st["caps"], st["used"] = True, False
                return False
            st["caps"] = False
            if st["used"]:
                stop_recording()
            else:
                st["passthrough"] = True
                try:
                    keyboard.send("caps lock")
                finally:
                    st["passthrough"] = False
            return False
        if st["caps"] and is_second(e):
            if e.event_type == "down":
                if not st["used"]:
                    st["used"] = True
                    start_recording()
            else:
                stop_recording()
            return False
        if st["caps"] and is_hist(e):
            st["used"] = True
            if e.event_type == "down":
                UI["open_history"] = True
            return False
        if st["caps"] and is_undo(e):
            st["used"] = True
            if e.event_type == "down":
                threading.Thread(target=undo_last, daemon=True).start()
            return False
        return True

    keyboard.hook(hook, suppress=True)
    log(f"atajo: Bloq Mayús + {second} (mantener) | historial: Bloq Mayús + {HISTORY_KEY} | deshacer: Bloq Mayús + Z")


# =====================================================================
# Overlay
# =====================================================================
class Overlay:
    W, H, PAD = 580, 140, 44
    BARS = 41
    KEY = "#010203"  # color transparente

    def __init__(self, root):
        import tkinter as tk
        import tkinter.font as tkfont
        self.tk, self.root = tk, root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-transparentcolor", self.KEY)
        except Exception:
            pass
        root.attributes("-alpha", 0.0)
        root.configure(bg=self.KEY)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.cw, self.ch = self.W + self.PAD * 2, self.H + self.PAD * 2
        root.geometry(f"{self.cw}x{self.ch}+{(sw - self.cw) // 2}+{sh - self.ch - 64}")
        self.c = tk.Canvas(root, width=self.cw, height=self.ch, bg=self.KEY, highlightthickness=0, bd=0)
        self.c.pack()
        fams = tkfont.families()
        fam = "Segoe UI Variable Display" if "Segoe UI Variable Display" in fams else "Segoe UI"
        self.f_text = (fam, 12)
        self.f_small = (fam, 9)
        self.f_mono = ("Consolas", 10)
        self._font_cache = {}
        self.alpha, self.visible = 0.0, False
        self.cur = [0.04] * self.BARS   # altura actual (suavizada)
        self.tgt = [0.04] * self.BARS   # objetivo
        self.t = 0.0
        self.hist_win = None
        root.withdraw()
        self._tick()

    # ---------- utilidades ----------
    def rr(self, x0, y0, x1, y1, r, **kw):
        r = max(0.5, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
               x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.c.create_polygon(pts, smooth=True, **kw)

    @staticmethod
    def mix(a, b, t):
        a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
        t = max(0.0, min(1.0, t))
        return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _font(self, spec):
        import tkinter.font as tkfont
        if spec not in self._font_cache:
            self._font_cache[spec] = tkfont.Font(family=spec[0], size=spec[1])
        return self._font_cache[spec]

    def _fit(self, txt, width, spec, from_end=False):
        f = self._font(spec)
        if f.measure(txt) <= width:
            return txt
        if from_end:
            while txt and f.measure("…" + txt) > width:
                txt = txt[1:]
            return "…" + txt
        while txt and f.measure(txt + "…") > width:
            txt = txt[:-1]
        return txt + "…"

    # ---------- dibujo ----------
    def draw(self):
        import math
        c = self.c
        c.delete("all")
        x0, y0 = self.PAD, self.PAD
        x1, y1 = x0 + self.W, y0 + self.H
        s = UI["state"]
        accent = {"listening": "#ff4d6d", "thinking": "#7aa2ff", "done": "#34e0a1", "error": "#ff4d6d"}.get(s, "#7aa2ff")
        accent2 = {"listening": "#ff9a5c", "thinking": "#c58cff", "done": "#8cf5d2", "error": "#ff9a5c"}.get(s, "#c58cff")

        # halo exterior
        for i in range(10, 0, -1):
            col = self.mix(self.KEY, accent, 0.16 - i * 0.014)
            self.rr(x0 - i * 2.2, y0 - i * 2.2, x1 + i * 2.2, y1 + i * 2.2, 40 + i * 2, fill=col, outline="")
        # cuerpo + borde
        self.rr(x0, y0, x1, y1, 40, fill="#0a0b10", outline="")
        self.rr(x0, y0, x1, y1, 40, fill="", outline=self.mix("#2a2d3a", accent, 0.25), width=1)
        c.create_line(x0 + 60, y0 + 1, x1 - 60, y0 + 1, fill=self.mix("#0a0b10", "#ffffff", 0.18))

        # ---------- cabecera ----------
        hy = y0 + 24
        label = {"listening": "ESCUCHANDO", "thinking": "PENSANDO", "done": "LISTO", "error": "ERROR"}.get(s, "")
        if s == "listening":
            p = 0.5 + 0.5 * math.sin(self.t * 6)
            r = 5 + 2.5 * p
            c.create_oval(x0 + 30 - r - 5, hy - r - 5, x0 + 30 + r + 5, hy + r + 5,
                          fill=self.mix("#0a0b10", accent, 0.35), outline="")
            c.create_oval(x0 + 30 - r, hy - r, x0 + 30 + r, hy + r, fill=accent, outline="")
            secs = time.time() - UI["t0"]
            c.create_text(x1 - 28, hy, text=f"{int(secs // 60)}:{int(secs % 60):02d}", anchor="e",
                          fill="#9aa0b4", font=self.f_mono)
        elif s == "thinking":
            ang = (self.t * 300) % 360
            c.create_arc(x0 + 21, hy - 9, x0 + 39, hy + 9, start=ang, extent=260, style="arc", outline=accent, width=3)
        elif s == "done":
            c.create_oval(x0 + 21, hy - 9, x0 + 39, hy + 9, fill=accent, outline="")
            c.create_line(x0 + 25, hy, x0 + 29, hy + 4, x0 + 35, hy - 4, fill="#0a0b10", width=2.4,
                          capstyle="round", joinstyle="round")
        elif s == "error":
            c.create_oval(x0 + 21, hy - 9, x0 + 39, hy + 9, fill=accent, outline="")
            c.create_text(x0 + 30, hy, text="!", fill="#0a0b10", font=(self.f_text[0], 11, "bold"))
        c.create_text(x0 + 46, hy, text=label, anchor="w", fill=self.mix("#9aa0b4", accent, 0.5),
                      font=(self.f_small[0], 9, "bold"))
        sub = {"listening": "· apretá Espacio para terminar", "thinking": "· interpretando tus correcciones",
               "done": "· pegado y copiado al portapapeles", "error": ""}.get(s, "")
        lw = self._font((self.f_small[0], 9)).measure(label) + 8
        c.create_text(x0 + 46 + lw, hy, text=sub, anchor="w", fill="#6b7088", font=self.f_small)
        if s == "done":
            parts = []
            if UI["discarded"]:
                n = UI["discarded"]
                chip = f"{n} idea descartada" if n == 1 else f"{n} ideas descartadas"
                cw = self._font((self.f_small[0], 9)).measure(chip) + 20
                self.rr(x1 - 28 - cw - 46, hy - 10, x1 - 28 - 46, hy + 10, 10, fill="#2a1219", outline="#5a1f2c")
                c.create_text(x1 - 28 - cw / 2 - 46, hy, text=chip, fill="#ff8aa0", font=(self.f_small[0], 9, "bold"))
            c.create_text(x1 - 28, hy, text=f"{UI['elapsed']:.1f} s", anchor="e", fill="#6b7088", font=self.f_mono)

        # ---------- onda ----------
        wx0, wx1 = x0 + 26, x1 - 26
        mid = y0 + 62
        maxh = 46
        n = self.BARS
        gap = (wx1 - wx0) / n
        for i in range(n):
            h = max(3, self.cur[i] * maxh)
            bx = wx0 + i * gap + gap * 0.3
            bw = gap * 0.4
            col = self.mix(accent, accent2, i / (n - 1))
            self.rr(bx - 1.5, mid - h / 2 - 1.5, bx + bw + 1.5, mid + h / 2 + 1.5, bw,
                    fill=self.mix("#0a0b10", col, 0.28), outline="")
            self.rr(bx, mid - h / 2, bx + bw, mid + h / 2, bw / 2, fill=col, outline="")

        # ---------- línea de texto ----------
        ty = y1 - 26
        if s in ("listening", "thinking"):
            live = UI["live"]
            if live:
                cursor = "▍" if (int(self.t * 2) % 2 == 0 and s == "listening") else " "
                txt = self._fit(live, self.W - 70, self.f_text, from_end=True) + cursor
                col = "#e6e8f0"
            else:
                txt = "hablá…" if s == "listening" else "interpretando tus correcciones…"
                col = "#5c627a"
            c.create_text(x0 + 30, ty, text=txt, anchor="w", fill=col, font=self.f_text)
        elif s in ("done", "error"):
            big = (self.f_text[0], 14, "bold")
            txt = self._fit(UI["text"], self.W - 60, (self.f_text[0], 14))
            c.create_text(x0 + 30, ty - 8, text=txt, anchor="w", fill="#ffffff" if s == "done" else "#ffb3c0", font=big)
            if s == "done":
                c.create_text(x0 + 30, ty + 16, text="Win + H  ver lo descartado     Win + Z  deshacer",
                              anchor="w", fill="#5c627a", font=(self.f_small[0], 8, "bold"))

    # ---------- animación ----------
    def _tick(self):
        import math
        s = UI["state"]
        self.t += 1 / 60
        n, mid = self.BARS, self.BARS // 2
        if s == "listening":
            lvl = UI["level"]
            UI["level"] *= 0.8
            for i in range(0, mid):
                self.tgt[i] = self.tgt[i + 1]
            for i in range(n - 1, mid, -1):
                self.tgt[i] = self.tgt[i - 1]
            self.tgt[mid] = 0.06 + 0.94 * lvl
        elif s == "thinking":
            for i in range(n):
                self.tgt[i] = 0.12 + 0.3 * (0.5 + 0.5 * math.sin(self.t * 7 - i * 0.35))
        else:
            for i in range(n):
                self.tgt[i] = 0.04 + 0.04 * (0.5 + 0.5 * math.sin(self.t * 2 + i * 0.4))
        for i in range(n):
            env = 1.0 - (abs(i - mid) / mid) ** 2 * 0.6
            self.cur[i] += (self.tgt[i] * env - self.cur[i]) * 0.35

        want = s != "idle"
        if s in ("done", "error") and time.time() - UI["since"] > (1.8 if s == "done" else 2.4):
            UI["state"] = "idle"
            want = False
        self.alpha += 0.16 if want else -0.10
        self.alpha = max(0.0, min(0.97, self.alpha))
        if self.alpha > 0 and not self.visible:
            self.root.deiconify()
            self.visible = True
        if self.alpha == 0 and self.visible:
            self.root.withdraw()
            self.visible = False
        if self.visible:
            self.root.attributes("-alpha", self.alpha)
            self.draw()
        if UI["open_history"]:
            UI["open_history"] = False
            self.show_history()
        self.root.after(16, self._tick)

    # ---------- historial ----------
    def show_history(self):
        tk = self.tk
        if self.hist_win is not None and self.hist_win.winfo_exists():
            self.hist_win.lift()
            self.hist_win.focus_force()
            return
        BG, PANEL, CARD, LINE = "#0c0d13", "#0f1016", "#15181f", "#1c1f29"
        FG, MUTED, DIM = "#e9eaf2", "#9aa0b4", "#5c627a"
        fam = self.f_text[0]
        win = tk.Toplevel(self.root)
        self.hist_win = win
        win.title("Memoria de voz")
        try:
            win.iconbitmap(os.path.join(BASE, "logo.ico"))
        except Exception:
            pass
        win.configure(bg=BG)
        win.geometry("1120x680")
        win.attributes("-topmost", True)
        state = {"tab": "dictados", "q": "", "items": [], "sel": None}

        # ---- cabecera
        head = tk.Frame(win, bg=BG)
        head.pack(fill="x", padx=24, pady=(18, 10))
        tk.Label(head, text="Memoria de voz", bg=BG, fg=FG, font=(fam, 15, "bold")).pack(side="left")
        hist_all = load_history(1000)
        week = [e for e in hist_all if e["ts"][:10] >= (datetime.now().date().isoformat()[:8] + "01")]
        mins = sum(e.get("segundos", 0) for e in hist_all) / 60
        tk.Label(head, text=f"   {len(hist_all)} dictados · {mins:.0f} min hablados", bg=BG, fg=DIM,
                 font=(fam, 10)).pack(side="left", padx=(6, 0))
        qvar = tk.StringVar()
        q = tk.Entry(head, textvariable=qvar, bg="#14161f", fg=FG, insertbackground=FG, bd=0,
                     highlightthickness=1, highlightbackground="#262a37", highlightcolor="#7aa2ff",
                     font=(fam, 11), width=32)
        q.pack(side="right", ipady=7, padx=(0, 0))
        tk.Label(head, text="Buscar  ", bg=BG, fg=DIM, font=(fam, 10)).pack(side="right")

        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        left = tk.Frame(body, bg=BG, width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(22, 0))

        # ---- pestañas
        tabs = tk.Frame(left, bg=BG)
        tabs.pack(fill="x", pady=(0, 10))
        tab_btns = {}

        def set_tab(name):
            state["tab"] = name
            for k, b in tab_btns.items():
                on = k == name
                b.configure(bg=FG if on else BG, fg=BG if on else MUTED,
                            highlightbackground="#262a37" if not on else FG)
            refresh()

        for key, label in (("dictados", "Dictados"), ("clips", "Portapapeles"), ("desc", "Descartado")):
            b = tk.Button(tabs, text=label, command=lambda k=key: set_tab(k), bd=0, highlightthickness=1,
                          padx=14, pady=6, font=(fam, 10, "bold"), cursor="hand2", activebackground="#262a37",
                          activeforeground=FG)
            b.pack(side="left", padx=(0, 6))
            tab_btns[key] = b

        lb = tk.Listbox(left, bg=PANEL, fg=FG, bd=0, highlightthickness=0, selectbackground="#2b2f45",
                        selectforeground="#ffffff", font=(fam, 10), activestyle="none")
        lb.pack(fill="both", expand=True)

        # ---- detalle
        meta = tk.Label(right, text="", bg=BG, fg=MUTED, font=("Consolas", 10), anchor="w")
        meta.pack(fill="x")
        btns = tk.Frame(right, bg=BG)
        btns.pack(fill="x", pady=(8, 12))

        def mkbtn(parent, txt, cmd, primary=False, danger=False):
            bg = FG if primary else ("#2a1219" if danger else BG)
            fg = BG if primary else ("#ff8aa0" if danger else "#c9ccd8")
            b = tk.Button(parent, text=txt, command=cmd, bg=bg, fg=fg, bd=0, highlightthickness=1,
                          highlightbackground="#5a1f2c" if danger else ("#262a37" if not primary else FG),
                          padx=14, pady=7, font=(fam, 10, "bold"), cursor="hand2",
                          activebackground="#3a3f5c", activeforeground="#ffffff")
            b.pack(side="left", padx=(0, 8))
            return b

        def section(title, color, accent):
            tk.Label(right, text=title, bg=BG, fg=color, font=(fam, 8, "bold")).pack(anchor="w", pady=(6, 4))
            fr = tk.Frame(right, bg=accent)
            fr.pack(fill="both", expand=True)
            t = tk.Text(fr, bg="#12141b", fg=FG, bd=0, highlightthickness=0, wrap="word",
                        font=(fam, 11), padx=16, pady=12, insertbackground=FG, height=4)
            t.pack(fill="both", expand=True, padx=(3, 0))
            return t

        t_final = section("MENSAJE FINAL", "#8cf5d2", "#34e0a1")
        t_raw = section("LO QUE DIJISTE, LITERAL", MUTED, "#1f2330")
        t_disc = section("DESCARTADO · RECUPERABLE", "#ff8aa0", "#ff4d6d")
        t_final.configure(font=(fam, 13, "bold"))

        def current():
            sel = lb.curselection()
            return state["items"][sel[0]] if sel else None

        def copy_final():
            it = current()
            if it:
                pyperclip.copy(it["final"])
                save_clip(it["final"], "dictado")

        def copy_raw():
            it = current()
            if it:
                pyperclip.copy(it["raw"])

        def paste_again():
            it = current()
            if it:
                win.withdraw()
                win.after(250, lambda: (_paste(it["final"] + " "), win.deiconify()))

        def recover():
            it = current()
            if it and it.get("descartado"):
                txt = " ".join(it["descartado"])
                pyperclip.copy(txt)
                save_clip(txt, "recuperado")
                meta.configure(text="Descartado copiado al portapapeles ✓")

        mkbtn(btns, "Copiar final", copy_final, primary=True)
        mkbtn(btns, "Copiar literal", copy_raw)
        mkbtn(btns, "Pegar de nuevo", paste_again)
        mkbtn(btns, "Recuperar descartado", recover, danger=True)

        def fill(_=None):
            it = current()
            for t in (t_final, t_raw, t_disc):
                t.delete("1.0", "end")
            if not it:
                return
            t_final.insert("1.0", it["final"])
            t_raw.insert("1.0", it["raw"])
            t_disc.insert("1.0", "\n".join(f"• {d}" for d in it.get("descartado", [])) or "—")
            meta.configure(text=f"{it['ts'].replace('T', ' ')} · {it.get('segundos', 0)} s · {it.get('origen', 'dictado')}")

        def refresh(*_):
            ql = qvar.get().strip().lower()
            tab = state["tab"]
            if tab == "clips":
                items = [{"ts": c["ts"], "final": c["texto"], "raw": c["texto"], "descartado": [],
                          "segundos": 0, "origen": "portapapeles · " + c.get("origen", "")} for c in load_clips(500)]
            else:
                items = [dict(e, origen="dictado") for e in load_history(1000)]
                if tab == "desc":
                    items = [e for e in items if e.get("descartado")]
            if ql:
                items = [e for e in items if ql in (e["final"] + " " + e["raw"] + " " + " ".join(e.get("descartado", []))).lower()]
            items.reverse()
            state["items"] = items
            lb.delete(0, "end")
            today = datetime.now().date().isoformat()
            for e in items:
                day = e["ts"][:10]
                when = e["ts"][11:16] if day == today else e["ts"][5:10] + " " + e["ts"][11:16]
                tag = f"  · {len(e['descartado'])} desc." if e.get("descartado") else ""
                lb.insert("end", f" {when}  {e['final'][:40].replace(chr(10), ' ')}{tag}")
            if items:
                lb.selection_set(0)
            fill()

        qvar.trace_add("write", refresh)
        lb.bind("<<ListboxSelect>>", fill)
        win.bind("<Escape>", lambda e: win.destroy())
        set_tab("dictados")
        q.focus_set()


# =====================================================================
# Logo e ícono de bandeja
# =====================================================================
def make_logo(size=256):
    """Logo WhisperPRO: squircle con degradé coral→durazno y 5 barras blancas de onda de voz."""
    from PIL import Image, ImageDraw
    S = size * 4                                   # supersampling para bordes limpios
    grad = Image.new("RGBA", (S, S))
    gp = grad.load()
    c1, c2 = (255, 77, 109), (255, 154, 92)        # #FF4D6D → #FF9A5C (diagonal)
    for y in range(S):
        for x in range(0, S, 4):
            t = (x + y) / (2 * S)
            col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)
            for k in range(4):
                if x + k < S:
                    gp[x + k, y] = col
    mask = Image.new("L", (S, S), 0)
    m = ImageDraw.Draw(mask)
    pad = int(S * 0.02)
    m.rounded_rectangle((pad, pad, S - pad, S - pad), radius=int(S * 0.24), fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    bars = [0.30, 0.52, 0.80, 0.52, 0.30]
    bw, gap = S * 0.075, S * 0.065
    x = (S - (len(bars) * bw + (len(bars) - 1) * gap)) / 2
    for h in bars:
        bh = S * 0.62 * h
        y0 = (S - bh) / 2
        d.rounded_rectangle((x, y0, x + bw, y0 + bh), radius=bw / 2, fill=(255, 255, 255, 255))
        x += bw + gap
    return img.resize((size, size), Image.LANCZOS)


def ensure_icon_file():
    path = os.path.join(BASE, "logo.ico")
    if not os.path.exists(path):
        try:
            make_logo(256).save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        except Exception as e:
            dbg(f"no pude crear logo.ico: {e}")
    return path


def start_tray(root):
    """Ícono en la bandeja del sistema con menú. Corre en su propio hilo."""
    try:
        import pystray
    except Exception as e:
        log(f"bandeja no disponible ({e}); instalá: pip install pystray pillow")
        return None
    name = os.getenv("DICTADO_NOMBRE", "WhisperPRO")

    def on_history(icon, item):
        UI["open_history"] = True

    def on_toggle(icon, item):
        UI["paused"] = not UI.get("paused", False)
        icon.title = f"{name} · {'pausado' if UI['paused'] else 'escuchando atajos'}"

    def on_quit(icon, item):
        icon.visible = False
        icon.stop()
        if root is not None:
            try:
                root.after(0, root.destroy)
            except Exception:
                pass
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(lambda item: f"{name} v{VERSION[1:]}", None, enabled=False),
        pystray.MenuItem(lambda item: f"Atajo: {HOTKEY}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Historial y portapapeles", on_history, default=True),
        pystray.MenuItem(lambda item: "Cambiar clave de IA" if has_any_key() else "Conectar clave de IA (gratis)",
                         lambda i, it: UI.__setitem__("open_setup", True)),
        pystray.MenuItem("Configuración avanzada (.env)", lambda i, it: os.startfile(ENV_PATH)),
        pystray.MenuItem("Ver log", lambda i, it: os.startfile(LOG_FILE)),
        pystray.MenuItem(lambda item: "Reanudar" if UI.get("paused") else "Pausar atajos", on_toggle),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", on_quit),
    )
    icon = pystray.Icon(name, make_logo(64), f"{name} · escuchando atajos", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon


# =====================================================================
# UI web (WebView2): overlay y panel con el diseño real
# =====================================================================
UI_DIR = os.path.join(RES, "ui")
APP_NAME = os.getenv("DICTADO_NOMBRE", "WhisperPRO")


class PanelAPI:
    """Lo que el panel HTML puede pedirle a Python (window.pywebview.api.*).
    OJO: sin atributos públicos que sean objetos (pywebview los recorre y entra en recursión)."""

    def __init__(self):
        self._win = None

    def load(self, tab, q):
        q = (q or "").strip().lower()
        if tab == "clips":
            items = [{"ts": c["ts"], "final": c["texto"], "raw": c["texto"], "descartado": [], "segundos": 0,
                      "origen": "portapapeles" if c.get("origen") == "anterior" else c.get("origen", "")}
                     for c in load_clips(500)]
        else:
            items = [dict(e, origen="") for e in load_history(1000)]
            if tab == "desc":
                items = [e for e in items if e.get("descartado")]
        if q:
            items = [e for e in items if q in (e["final"] + " " + e["raw"] + " " + " ".join(e.get("descartado", []))).lower()]
        items.reverse()
        allh = load_history(5000)
        mins = sum(e.get("segundos", 0) for e in allh) / 60
        return {"items": items[:300], "stat": f"{len(allh)} dictados · {mins:.0f} min hablados"}

    def action(self, a, it):
        if a == "copy_final":
            pyperclip.copy(it["final"]); save_clip(it["final"], "dictado"); return "Copiado"
        if a == "copy_raw":
            pyperclip.copy(it["raw"]); return "Literal copiado"
        if a == "recover":
            txt = " ".join(it.get("descartado") or [])
            if not txt:
                return "Nada que recuperar"
            pyperclip.copy(txt); save_clip(txt, "recuperado"); return "Descartado copiado al portapapeles"
        if a == "paste_again":
            if self._win:
                self._win.hide()
            threading.Thread(target=lambda: (time.sleep(0.35), _paste(it["final"] + " ")), daemon=True).start()
            return None
        if a == "close":
            self.close()
        return None

    def close(self):
        if self._win:
            self._win.hide()

    # --- conexión de la clave (pantalla "Conectá WhisperPRO") ---
    def key_status(self):
        return {"has": has_any_key(), "groq": mask_key(GROQ_KEY), "hotkey": HOTKEY}

    def open_groq(self):
        import webbrowser
        webbrowser.open(GROQ_KEYS_URL)
        return True

    def scan_clipboard(self):
        """Mientras la pantalla está abierta: si el usuario copió una clave gsk_..., la prueba y la guarda sola."""
        try:
            m = _KEY_RE.search(pyperclip.paste() or "")
        except Exception:
            m = None
        if not m:
            return {"st": "waiting"}
        key = m.group(0)
        if key == GROQ_KEY:
            return {"st": "ok", "key": mask_key(key)}
        if key == _key_flow["tried"]:
            return {"st": "bad", "msg": _key_flow["msg"]}
        return self.save_key(key)

    def save_key(self, key):
        key = (key or "").strip()
        m = _KEY_RE.search(key)
        if not m:
            return {"st": "bad", "msg": "Las claves de Groq empiezan con gsk_"}
        key = m.group(0)
        ok, msg = validate_groq_key(key)
        _key_flow["tried"], _key_flow["msg"] = key, msg
        if not ok:
            return {"st": "bad", "msg": msg}
        apply_groq_key(key)
        return {"st": "ok", "key": mask_key(key)}


# Niveles de audio para la onda: el callback de audio los deja acá, la ventana los pide.
_levels = []
_levels_lock = threading.Lock()
_hint = {"key": "Win"}
_mode = {"v": "mini"}
_confirm = {"at": 0.0}     # primer Esc: pregunta "¿borrar?" durante 3 s


def confirm_active():
    return _recording and time.time() - _confirm["at"] < 3.0


class OverlayAPI:
    """La ventana del overlay llama a poll() ~30 veces por segundo (no bloquea a Python)."""

    _first = True

    def poll(self):
        if OverlayAPI._first:
            OverlayAPI._first = False
            log("overlay: la ventana empezó a pedir datos (OK)")
        with _levels_lock:
            lv = _levels[:]
            _levels.clear()
        st = UI["state"]
        if st in ("done", "error") and time.time() - UI["since"] > (2.4 if st == "done" else 2.8):
            UI["state"] = st = "idle"
        return {"state": st, "live": UI["live"], "text": UI["text"], "discarded": UI["discarded"],
                "elapsed": round(UI["elapsed"], 2), "levels": lv, "mode": _mode["v"], "hint": _hint["key"],
                "confirm": confirm_active()}


def run_web_ui():
    """Overlay + panel con pywebview (WebView2). Devuelve False si no se puede (y se usa Tk)."""
    try:
        import webview
    except Exception as e:
        log(f"pywebview no disponible ({e}); uso overlay básico")
        return False
    if not os.path.exists(os.path.join(UI_DIR, "overlay.html")):
        log("falta la carpeta ui/; uso overlay básico")
        return False

    import ctypes
    from ctypes import wintypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    u = ctypes.windll.user32
    # prototipos correctos para 64 bits (sin esto SetWindowPos falla y la ventana queda fuera de pantalla)
    u.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    u.FindWindowW.restype = wintypes.HWND
    u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    u.SetWindowPos.restype = wintypes.BOOL
    u.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    u.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    u.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    u.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    HWND_TOPMOST = wintypes.HWND(-1)
    g = ctypes.windll.gdi32
    g.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
    g.CreateRoundRectRgn.restype = wintypes.HRGN
    u.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    MINI = (196, 44)      # píldora: la ventana mide exactamente esto
    FULL = (600, 150)     # cápsula desplegada
    DONE_MINI = (236, 44)  # píldora con el tilde de "copiado"
    BOTTOM = 52           # separación de la barra de tareas
    _hint["key"] = "Win" if HOTKEY.lower().startswith("win") else "Bloq Mayús"

    api = PanelAPI()
    panel = webview.create_window(f"{APP_NAME} — Memoria de voz", os.path.join(UI_DIR, "panel.html"), js_api=api,
                                  width=1120, height=680, background_color="#0c0d13", min_size=(900, 560))
    api._win = panel
    overlay = webview.create_window(f"{APP_NAME} overlay", os.path.join(UI_DIR, "overlay.html"), js_api=OverlayAPI(),
                                    width=FULL[0], height=FULL[1], x=-5000, y=-5000,
                                    frameless=True, transparent=True, on_top=True, focus=False,
                                    easy_drag=False, background_color="#0b0c11")

    def on_closing():
        panel.hide()   # cerrar el panel no cierra el programa: queda en la bandeja
        return False

    panel.events.closing += on_closing

    def rect_for(mode):
        w, h = MINI if mode == "mini" else FULL
        return (sw - w) // 2, sh - h - BOTTOM, w, h

    def placer():
        """Ubica el overlay según el estado y despliega/contrae según la posición del mouse."""
        hwnd = 0
        for _ in range(80):
            hwnd = u.FindWindowW(None, f"{APP_NAME} overlay")
            if hwnd:
                break
            time.sleep(0.1)
        if not hwnd:
            log("overlay: NO encontré la ventana (FindWindow falló)")
            return
        log(f"overlay: ventana encontrada hwnd={hwnd} pantalla={sw}x{sh}")
        ex = u.GetWindowLongPtrW(hwnd, -20)
        u.SetWindowLongPtrW(hwnd, -20, ex | 0x08000000 | 0x00000080)   # NOACTIVATE | TOOLWINDOW
        pt = wintypes.POINT()
        cur = "off"
        out_since = 0.0
        geo = {"w": 0.0, "h": 0.0}

        # La ventana NO cambia de tamaño (WebView2 no se redimensiona bien desde afuera):
        # mide siempre FULL y lo que se anima es la región visible, abajo al centro.
        WX, WY = (sw - FULL[0]) // 2, sh - FULL[1] - BOTTOM
        vis = {"w": 0.0, "h": 0.0}

        def region(w, h):
            w, h = int(round(w)), int(round(h))
            r = int(min(h / 2, 34 if h > 80 else h / 2))
            x0, y0 = (FULL[0] - w) // 2, FULL[1] - h
            u.SetWindowRgn(hwnd, g.CreateRoundRectRgn(x0, y0, x0 + w + 1, y0 + h + 1, 2 * r, 2 * r), True)
            vis["w"], vis["h"] = w, h

        def show_at_home():
            u.SetWindowPos(hwnd, HWND_TOPMOST, WX, WY, FULL[0], FULL[1], 0x0010 | 0x0040)

        def animate(to, ms=180):
            fw, fh = vis["w"] or to[0], vis["h"] or to[1]
            steps = max(1, ms // 12)
            for i in range(1, steps + 1):
                k = 1 - (1 - i / steps) ** 3          # ease-out cúbico (igual que el CSS)
                region(fw + (to[0] - fw) * k, fh + (to[1] - fh) * k)
                time.sleep(0.012)

        while True:
            try:
                st = UI["state"]
                if st == "idle":
                    want = "off"
                elif confirm_active():
                    want = "full"            # la pregunta de Esc se ve siempre desplegada
                else:
                    u.GetCursorPos(ctypes.byref(pt))
                    w, h = (vis["w"] or MINI[0]), (vis["h"] or MINI[1])
                    x, y = WX + (FULL[0] - w) // 2, WY + FULL[1] - h
                    inside = x - 6 <= pt.x <= x + w + 6 and y - 6 <= pt.y <= y + h + 6
                    if cur == "full":
                        if inside:
                            out_since = 0.0
                            want = "full"
                        else:
                            out_since = out_since or time.time()
                            want = "mini" if time.time() - out_since > 0.45 else "full"
                    else:
                        want = "full" if inside else "mini"
                    if want == "mini" and st == "done":
                        want = "minidone"        # un poco más ancha: tilde + "Copiado al portapapeles"
                if want != cur:
                    dbg(f"overlay: {cur} -> {want}")
                    prev, cur = cur, want
                    if want == "off":
                        u.SetWindowPos(hwnd, HWND_TOPMOST, -5000, -5000, FULL[0], FULL[1], 0x0010)
                        vis["w"] = vis["h"] = 0
                        _mode["v"] = "mini"
                    else:
                        _mode["v"] = "full" if want == "full" else "mini"
                        target = {"mini": MINI, "minidone": DONE_MINI, "full": FULL}[want]
                        if prev == "off":
                            region(*target)
                            show_at_home()
                        else:
                            animate(target)
                if UI["open_history"]:
                    UI["open_history"] = False
                    panel.show()
                    panel.restore()
                    try:
                        panel.evaluate_js("load()")
                    except Exception:
                        pass
                if UI["open_setup"]:
                    UI["open_setup"] = False
                    panel.show()
                    panel.restore()
                    try:
                        panel.evaluate_js("openSetup()")
                    except Exception:
                        pass
            except Exception as e:
                dbg(f"placer: {e}")
            time.sleep(0.03)

    def on_start():
        log("ui: ventanas creadas, arranco el overlay")
        threading.Thread(target=placer, daemon=True, name="placer").start()
        start_tray(None)

    try:
        webview.start(on_start, gui="edgechromium", private_mode=False)
    except Exception as e:
        log(f"WebView2 no disponible ({e}); uso overlay básico")
        return False
    return True


# =====================================================================
# main
# =====================================================================
def main():
    motor = next((n for n, k, _ in STT if k), f"Whisper local ({LOCAL_MODEL})")
    llm = "Groq (auto)" if GROQ_KEY else "OpenAI" if OPENAI_KEY else "Gemini" if GEMINI_KEY else "—"
    print(f"[dictado {VERSION}] python {sys.version.split()[0]} | STT: {motor} | corrección: {llm if SMART else 'off'} | en vivo: {'sí' if LIVE else 'no'}", flush=True)
    try:
        dev = sd.query_devices(kind="input")
        log(f"micrófono: {dev['name']}")
    except Exception as e:
        log(f"ERROR: no encuentro micrófono de entrada: {e}")
    setup_hotkeys()
    if GROQ_KEY:
        # precalentar: conexión HTTPS abierta y lista de modelos en caché antes del primer dictado
        threading.Thread(target=lambda: (groq_models("llm"), groq_models("stt")), daemon=True, name="warmup").start()
    if not has_any_key():
        log("sin clave de IA: abro la conexión guiada")
        UI["open_setup"] = True
    if os.getenv("DICTADO_UI", "web") == "web" and run_web_ui():
        return
    try:
        import tkinter as tk
        root = tk.Tk()
        try:
            root.iconbitmap(ensure_icon_file())
        except Exception:
            pass
        Overlay(root)
        start_tray(root)
        root.mainloop()
    except Exception as e:
        log(f"overlay no disponible ({e}); sigo sin visual")
        keyboard.wait()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception:
        import traceback
        traceback.print_exc()
        log("ERROR FATAL (ver dictado.log). Cerrando en 30 s.")
        time.sleep(30)
        raise
