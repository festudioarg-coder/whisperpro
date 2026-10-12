# WhisperPRO web (iPhone y cualquier navegador)

Una sola página (`index.html`) que se instala como app en el iPhone. Sin servidor propio y sin cuenta:

1. La persona pega **su propia clave de Groq** (se guarda solo en su teléfono).
2. Toca el micrófono, habla y vuelve a tocar.
3. El audio va **directo del teléfono a Groq**, se transcribe y se corrige con la misma lógica que la app de Windows (autocorrecciones habladas, muletillas, variante regional).
4. Queda el texto final para **Copiar** o **Compartir**, más la versión literal y lo descartado. El historial se guarda en el teléfono.

## Privacidad (lo que se puede afirmar)
- Historial y clave: solo en el teléfono. No hay cuenta, ni telemetría, ni servidores de FESTUDIOS en el medio.
- La política de seguridad de la página (`Content-Security-Policy` en `index.html`) permite conectarse **únicamente a `api.groq.com`**.
- Lo que sí sale es el audio a Groq mientras se dicta. No decir "nada sale del teléfono".

## Cómo publicarla
Necesita **HTTPS** (el micrófono y la instalación lo exigen). Opciones:
- **festudios.pro/whisper/** subiendo el contenido de esta carpeta por SFTP (la más simple, ya tenés el hosting).
- Cloudflare Pages o Netlify arrastrando la carpeta.
- GitHub Pages solo sirve si el repo es público (o con plan de pago): este repo es privado.

## Instalar en el iPhone
Safari → abrir la dirección → Compartir → **Agregar a pantalla de inicio**. La primera vez que graba, iOS pide permiso de micrófono.

## Qué falta verificar en un iPhone real
Probado en Chromium con un micrófono y un Groq simulados (grabación, transcripción, corrección, copiado, historial, política de seguridad, service worker). **No probado en Safari de iPhone ni contra el Groq real**. Puntos a mirar:
- **CORS de Groq:** si el navegador bloquea las llamadas a `api.groq.com` desde la página, aparece "No hay conexión con Groq". Plan B: un proxy mínimo (Cloudflare Worker) que agregue los encabezados, aunque eso pone un servidor en el medio y cambia el mensaje de privacidad.
- **Copiado automático:** iOS solo deja copiar tras un toque; si no alcanza, el botón **Copiar** lo hace con un toque.
- **Grabación en iOS:** usa `audio/mp4` (Groq lo acepta). Si falla en una versión vieja de iOS, hay que sumar un formato WAV.

## Archivos
`index.html` (app) · `manifest.webmanifest` e íconos (instalación) · `sw.js` (abre sin conexión; no toca las llamadas a Groq) · `fonts/` (Bricolage Grotesque y Martian Mono, OFL, sin CDN).
