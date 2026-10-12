# WhisperPRO — dictado con texto en vivo, autocorrección e historial (Windows)

**Win + Espacio** (soltás las teclas) y hablá: el texto aparece en el input a medida que hablás. **Espacio** corta; la IA aplica tus correcciones habladas ("no, mejor no, borrá eso… hagamos X") y deja la versión final.
**Win + Z** deshacer · **Win + H** historial y portapapeles.

Al abrirlo aparece el panel **Memoria de voz**; lo cerrás y queda en la bandeja (ícono coral) escuchando el atajo. Clic derecho en el ícono: Historial, Configuración, Ver log, Pausar, Salir.

## Una sola carpeta: `F:\Proyectos\Cowork_claude\WhisperPRO\app`

| Archivo | Para qué |
|---|---|
| `instalar.bat` | Una vez (o cuando cambia `requirements.txt`): crea `venv` e instala todo. |
| `dev.bat` | **Desarrollo**: consola con diagnóstico y reinicio automático cada vez que se guarda `dictado.py`, `.env` o algo en `ui/`. Cuando Claude parchea un archivo, se ve al instante. |
| `dictado.bat` | Correr con consola (uso normal con logs a la vista). |
| `dictado_silencioso.vbs` | Correr sin consola (bandeja). Cierra una instancia previa si la hay. |
| `instalar_inicio.bat` | Que arranque con Windows. |
| `ver_log.bat` | Últimas 80 líneas de `dictado.log` (todo lo que pasa queda ahí, con o sin consola). |
| `build.bat` | Genera `dist\WhisperPRO\WhisperPRO.exe` (con empresa, producto, versión y copyright en Propiedades → Detalles) y, con Inno Setup 6, el instalador `build\out\WhisperPRO-Setup-x.y.z.exe` con `LICENCIA.txt`. Firma los dos si definís `WP_CERT` (.pfx) + `WP_CERT_PASS` o `WP_CERT_SHA1`. |
| `.env` | Tus keys y ajustes (nunca se copia a otro lado). |
| `ui/` | Overlay y panel (HTML + fuentes). Editar y guardar = se ve en el próximo reinicio. |

Versión instalada con el `.exe`: los datos del usuario (`.env`, historial, log) viven en `%APPDATA%\WhisperPRO`.

## Flujo para mejorar algo
1. `dev.bat` abierto.
2. Claude escribe el parche en `app\` (o lo hacés vos).
3. Se reinicia solo; probás; si falla, `dictado.log` tiene el error.
4. Cuando está bien: `build.bat` → instalador nuevo.

## Ajustes (en `.env`)
`DICTADO_HOTKEY` (`win+space` o `caps lock+space`), `DICTADO_LIVE=0` (sin texto en vivo), `DICTADO_SMART=0` (literal), `DICTADO_LANG=es`, `DICTADO_DEBUG=1` (teclas en consola), `DICTADO_UI=tk` (overlay básico si WebView2 falla).
