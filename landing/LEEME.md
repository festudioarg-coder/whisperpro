# Landing de WhisperPRO — festudios.pro/whisperpro/

Sitio estático (HTML + CSS, sin JavaScript ni servicios externos: las tipografías van incluidas). Para publicarlo:

1. **Completar lo pendiente.** Desde la raíz del repo: `python landing/revisar.py` lista lo que falta:
   - `[PRECIO]` del plan Pro (en `index.html`),
   - `[EMAIL DE CONTACTO]` (en `privacidad/index.html`),
   - el link del instalador en el botón "Descargar para Windows" (id `descarga-win`) y el de la versión web para iPhone.
2. **Subir el contenido de esta carpeta** (no la carpeta en sí) a la carpeta `whisperpro/` del hosting de festudios.pro, por SFTP como el resto del sitio. Tiene que quedar:
   `festudios.pro/whisperpro/index.html`, `.../privacidad/index.html`, `.../img/`, `.../fonts/`, `favicon.ico`.
3. **Ruta.** Las páginas usan `<base href="/whisperpro/">`: tienen que servirse desde esa ruta. `festudios.pro/whisperpro` (sin barra) debe redirigir a `festudios.pro/whisperpro/` (casi todos los hosting lo hacen solos; si no, agregar la redirección).
4. **Después de publicar:** sumar `https://festudios.pro/whisperpro/sitemap.xml` al sitemap o al `robots.txt` raíz de festudios.pro (el `robots.txt` solo vale en la raíz del dominio), pedir la indexación en Search Console y probar el enlace compartiendo la URL en WhatsApp (se ve la imagen `img/og.png`).

## Qué contiene
- `index.html`: la landing (portada con el Guía, corrección hablada, cómo funciona, conexión guiada, funciones, privacidad, precios Gratis/Pro, preguntas, "Detrás de WhisperPRO" y descarga).
- **Páginas legales** (se generan con `python landing/generar_legales.py`; el texto vive en ese archivo): `privacidad/`, `terminos/`, `baja-y-arrepentimiento/` (baja de suscripción y botón de arrepentimiento), `contacto/` (quiénes somos y datos del proveedor) y `licencias/` (componentes de terceros). Más `sitemap.xml`. La Microsoft Store pide la URL de privacidad: `https://festudios.pro/whisperpro/privacidad/`.
- **Borradores a revisar con un profesional matriculado en Argentina antes de publicar**, sobre todo lo de arrepentimiento, defensa del consumidor, datos personales y el plan Pro. Completar `[CUIT]`, `[DOMICILIO COMERCIAL]` y lo del plan Pro (los detecta `revisar.py`).
- Para buscadores y tiendas: cada página tiene título, descripción, canonical y `robots`; el sitio no usa cookies ni analítica. **Si se agrega Google Analytics, píxeles o cookies, hay que actualizar la política (sección 8) y sumar un aviso de consentimiento.**
- `img/`: Guía, logo, ondas y la imagen para compartir en redes. `fonts/`: Bricolage Grotesque y Martian Mono (licencia OFL, incluida).

## Cuidado con lo que se afirma
Los textos de privacidad están escritos para ser ciertos hoy: historial, clave y ajustes quedan en la PC; no hay cuenta ni telemetría; el audio va directo a Groq. No decir "nada sale de tu PC". Si cambia el producto (por ejemplo, un plan Pro con servidor propio), hay que actualizar la landing y la política antes de publicarlo.

## Plan Pro
La lista de qué va en Gratis y qué en Pro es una propuesta: lo que ya existe hoy es el segundo atajo y las capturas de pantalla; lo demás figura como "próx." y no debe prometerse como disponible hasta que esté.
