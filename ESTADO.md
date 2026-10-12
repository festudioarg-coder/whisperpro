# ESTADO — WhisperPRO
> Único archivo de estado. Se reescribe después de cada paso. Última actualización: 12/10/2026 (madrugada).

## Qué es
Herramienta de dictado por voz para Windows (producto de FESTUDIOS): Win + Espacio graba, el texto aparece en vivo en cualquier input, Espacio corta y la IA aplica las correcciones habladas. Panel "Memoria de voz" (historial, portapapeles, descartado), ícono de bandeja con logo propio, overlay HTML (WebView2) con el diseño del canvas "WhisperPRO Design" de claude.ai. Plan de producto y negocio en `PLAN-PRODUCTO-WHISPERPRO.md`.

## Dónde vive cada cosa
- **ÚNICA carpeta de trabajo: `WhisperPRO/app/`** (v6.14). Contiene código (`dictado.py`), UI (`ui/`), `.env` con las keys de Juan (Groq + Gemini), historial, y los scripts: `instalar.bat`, `dev.bat` (reinicio automático al guardar), `dictado.bat`, `dictado_silencioso.vbs`, `ver_log.bat`, `build.bat` (PyInstaller + Inno Setup → instalador), `build/WhisperPRO.spec`, `build/instalador.iss`.
- Logs: `app/dictado.log` (todo lo que imprime, con o sin consola; errores fatales incluidos).
- Carpetas viejas, borrar cuando se pueda: `F:\Descargas\dictado` (tiene marcador _OBSOLETO), `F:\Descargas\WhisperPRO\dictado_1`, `C:\Users\BigLigas\Desktop\dictado`, `C:\Users\BigLigas\Documents\dictado`, `Desktop\dictado.bat`. No se pudieron mover por permisos.
- Motores: STT Groq whisper-large-v3-turbo (fallback OpenAI → Gemini → Whisper local solo en modo script); corrección Llama 3.3 70B (Groq).
- Versión instalada por `.exe`: datos del usuario en `%APPDATA%\WhisperPRO`.

## Próximo paso exacto
1. **Microsoft Store (prioridad), seguir `GUIA-MICROSOFT-STORE.md`:** Juan abre cuenta **Individual** (decidido 12/10), se registra en storedeveloper.microsoft.com, reserva el nombre y le pasa a Claude los 3 datos de Product identity.
2. Claude, en paralelo: cambios para MSIX (startupTask, detectar empaquetado, WebView2, micrófono denegado), AppxManifest, logos, `build_store.bat`, borradores de política de privacidad, ficha y notas para el revisor.
3. Juan: probar v6.14 en dev.bat (dictado en español neutro con whisper-large-v3, tilde "Copiado al portapapeles", conexión guiada con el Guía).

## Marca (11/10)
- Logo definido: squircle degradé coral #FF4D6D → durazno #FF9A5C con 5 barras blancas (sale de `branding/hero-01.png`, generado por Juan en ChatGPT). Redibujado en código (`make_logo` en dictado.py) → `app/logo.ico` y `branding/logo-1024.png`.
- `branding/ui-ventana-referencia.png`: ventana compacta (tarjeta ESCUCHANDO con onda, caja de texto con lo tachado, barra de controles: ajustes, traducir, stop, onda, notas). Referencia para la vista desplegada.
- Pendiente de la imagen hero: la figura encapuchada sin cara puede leerse como "hacker/espía" en un producto que escucha tu micrófono; usarla para redes de festudios, no para landing/Product Hunt.

## Backlog (después de validar el .exe)
- Links: si el usuario selecciona un texto que es una URL sin link (ej. "festudios.pro/precios"), WhisperPRO lo detecta y ofrece abrirlo (atajo o chip en el overlay). Pedido de Juan 11/10.
- Nombre definitivo (no "Whisper"). Firma: Azure Artifact Signing es solo para personas de EE.UU./Canadá → camino recomendado: Microsoft Store (MSIX, firma gratis de Microsoft, sin cartel de SmartScreen). Certificado OV US$150-300/año solo si hace falta el .exe suelto.
- Win+H choca con el dictado nativo de Windows → mover el historial a otro atajo.
- Esc en modo Bloq Mayús. Imágenes de marca en el instalador.
- Planes pagos: por ahora NO hay backend; cada usuario usa su propia clave gratis de Groq (ver decisión 12/10). Revisar si más adelante conviene un plan Pro con servidor propio.
- Para la versión que se publique: `DICTADO_DEBUG` apagado (con debug el log anota las primeras 40 teclas).

## A medio hacer
- v6.10: píldora minimizada mostraba solo el fondo (WebView2 no reacomoda al achicar la ventana) → ventana fija 600×150, se anima solo la forma recortada. Sin confirmar por Juan.
- v6.11: texto en vivo fallaba con micrófono de nivel bajo (log: voz ~0,01, umbral viejo 0,006 la tomaba como silencio) → mínimo 0,0025. Verificado: después del cambio, "tramos con texto en vivo: 4".
- v6.12: conexión guiada de la clave (panel "Conectá WhisperPRO"): botón abre console.groq.com/keys, la app mira el portapapeles y cuando copiás una clave gsk_ la prueba contra Groq, la guarda en el .env y la activa sin reiniciar. Pegado manual como respaldo. Sin clave, Win+Espacio abre esa pantalla. Bandeja: "Conectar/Cambiar clave de IA". Instalador: la página de clave ahora es opcional.
- v6.13: al cortar, el punto (girando mientras interpreta) se transforma en tilde verde + "Copiado al portapapeles" (píldora 236×44); desplegada dice COPIADO. El Guía (mascota FESTUDIOS, `ui/img/guia.png` recortado del fondo negro) aparece en la conexión guiada con globo de diálogo y ojo que late, y en el historial vacío.
- v6.14: público = español de todas las regiones (AR, LATAM, España) + inglés. Prompt de Whisper neutro ("Dictado en español, con puntuación."); la corrección entiende autocorrecciones de cualquier variante y respeta vos/tú/usted/vosotros y el vocabulario local; motor principal whisper-large-v3 (menos errores en español, mismo cupo gratis), turbo de respaldo. Verificado: md5 y log "dictado v6.14".
- Documentos: `GUIA-MICROSOFT-STORE.md` (paso a paso), `INVESTIGACION-FOROS-MOTORES-MEJORAS.md` (quejas de usuarios, motores, mejoras ordenadas), `REGLAS-DE-CONFIANZA.md` (Trustpilot, Store, leyes de reseñas), `INVESTIGACION-DISTRIBUCION-Y-MERCADO.md`. Todos también en el proyecto de claude.ai.
- `_tmp_estado_unused.md` es descartable (subido por error).

## Te toca a vos (Juan)
- Correr `instalar.bat` y `dev.bat` en `WhisperPRO\app`.
- Instalar Inno Setup 6 (jrsoftware.org/isdl.php) para poder generar el instalador.
- Elegir nombre del producto (no "Whisper"): Hablalo / Dictá / Dilo / Voz.app. Decidir precios del plan.

## Reglas que no se discuten
- Una sola carpeta: `WhisperPRO/app`. No crear copias en Descargas/Escritorio.
- `.env` con keys nunca va al proyecto de claude.ai ni a git.
- Cada parche se prueba con `dev.bat` y se mira `dictado.log` antes de decir que funciona.

## Historia (no leer al arrancar)
- 12/10: decisión — cuenta de Microsoft Store Individual. Por qué: Juan es monotributista, sin sociedad; la app sale gratis y no cobra nada todavía. Cuando haya planes pagos con cobro propio, se evalúa abrir cuenta Empresa (SAS) y transferir la app.
- 12/10: decisión (Juan) — WhisperPRO no se enfoca en el español rioplatense: apunta a Argentina, LATAM y España. Por qué: el mercado es todo el español.
- 12/10: decisión (Juan) — reputación limpia: invitar a reseñar a todos por igual, sin incentivos ni filtros (`REGLAS-DE-CONFIANZA.md`). Por qué: Trustpilot eliminó el perfil de Wispr Flow por incumplir sus directrices.
- 12/10: decisión (Juan) — cada usuario usa su propia clave gratis de Groq, con una conexión guiada lo más resuelta posible. Por qué: con nuestra clave pagaríamos el uso de todos; así el costo para FESTUDIOS es cero.
- 11/10: v1→v5 (texto en vivo, corrección LLM, historial, portapapeles, Win+Espacio) → v6 (overlay/panel HTML en WebView2, bandeja con logo) → v6.2 (log a archivo, dev.bat con auto-reinicio, build.bat + Inno Setup, rutas para app congelada). Investigación de mercado, plan de producto y diseño en canvas hechos.
