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

## Atajos y capturas (desde v6.15)
Se configuran en el panel (engranaje, o la tecla `,`) y se guardan en `settings.json`, solo en esta PC:
- **Hasta 2 atajos de grabación.** Modo *Pulsar*: el atajo empieza y la tecla final, sola, corta. Modo *Mantener*: grabás mientras lo tenés apretado.
- **Captura de región** (abre el selector de recortes de Windows, como Win+Shift+S) y **captura completa** (todos los monitores, al portapapeles y opcionalmente a `Imágenes\WhisperPRO`). Cada una se activa y se asigna a la combinación que quieras, por ejemplo Impr Pant.
- Historial y deshacer usan el modificador del primer atajo (Win+H / Win+Z por defecto).
- `DICTADO_HOTKEY` en `.env` sigue siendo el atajo inicial si todavía no existe `settings.json`.

## Datos y privacidad
Historial, portapapeles, clave de IA y ajustes viven en esta carpeta (o en `%APPDATA%\WhisperPRO` en la versión instalada). No hay cuenta ni telemetría. Lo único que sale de la PC es el audio de cada dictado, directo al motor de IA (Groq) con tu propia clave. El panel tiene una política de seguridad que le impide a la interfaz conectarse a internet.

## Pruebas
`python -m unittest discover -s tests` (desde esta carpeta): 32 pruebas del motor de atajos, sin necesidad de Windows.
