# WhisperPRO — Dónde publicarlo, cómo funciona el rubro y por qué nos elegirían
> Investigado el 12/10/2026. Fuentes al final. Corrige un dato del plan de producto del 11/10 (firma de código, sección 1.4).

## Resumen en cinco líneas
1. **El canal principal no es Chrome, es la Microsoft Store.** Es gratis para personas, Microsoft firma el paquete (se acaba el aviso azul de "editor desconocido") y deja cobrar con nuestro propio sistema de pagos quedándonos con el 100 %.
2. **La extensión de Chrome sirve como versión liviana y canal de descubrimiento**, no como producto: solo funciona dentro de Chrome y sus atajos globales están limitados a Ctrl+Shift+número.
3. **El líder es Wispr Flow**: valuación de US$2.000 M (agosto 2026), millones de usuarios, 270+ empresas Fortune 500, India como segundo mercado.
4. **No existe un competidor pensado para Latinoamérica en español.** Wispr probó que localizar funciona (India: modelo propio, precio de US$3,40, oficina local) y no lo hizo en nuestra región.
5. **"Inevitable" no se puede prometer** contra una empresa con US$361 M en el banco; sí se puede ser la opción obvia para un segmento que ellos no atienden: hispanohablantes en Windows que piensan en voz alta.

---

## 1. Dónde publicarlo

### 1.1 Microsoft Store (recomendado como canal principal)
- **Cuenta de desarrollador individual: gratis** (Microsoft eliminó la tarifa en septiembre de 2025, para todos los países).
- **Paquete MSIX: Microsoft lo vuelve a firmar con su certificado** después de aprobarlo. Resultado: sin aviso de SmartScreen y sin tener que comprar un certificado. Es la única forma gratuita de llegar al usuario sin el cartel de "editor desconocido".
- También acepta instaladores EXE/MSI, pero ahí **sí hay que firmarlos con un certificado de una autoridad reconocida** (no se aceptan autofirmados).
- **Cobros:** desde 2021 las apps que no son juegos pueden usar su propio sistema de pago y quedarse con el 100 % (Mercado Pago, Paddle, Stripe). La comisión del 12–15 % solo aplica si usás el sistema de cobro de Microsoft.
- **Qué hay que hacer:** convertir el build actual (PyInstaller) a MSIX con makeappx y un manifiesto propio (ver `GUIA-MICROSOFT-STORE.md`), abrir la cuenta en storedeveloper.microsoft.com, ficha con capturas y política de privacidad, y enviar. Pendiente de verificar: qué pide la verificación de identidad para Argentina.

### 1.2 Firma de código fuera de la Store (corrección)
- **Azure Artifact Signing (ex Trusted Signing, ~US$9,99/mes) es solo para personas de Estados Unidos y Canadá**, y para empresas de EE. UU., Canadá, UE y Reino Unido. **Desde Argentina como persona no se puede.** En el plan del 11/10 la recomendé: era un error.
- La alternativa mundial es un **certificado OV (US$150–300/año)**, con la clave en un token o módulo de hardware (obligatorio desde 2023). Validación de varios días hábiles.
- **El certificado EV ya no saltea SmartScreen** (Microsoft quitó eso en 2024): no vale la pena pagar más por eso.
- Ningún certificado da confianza instantánea: la reputación se construye con descargas firmadas siempre por el mismo editor.
- **Conclusión:** con la Store (MSIX) no hace falta certificado. Para el instalador descargable desde nuestra web, conviene el OV recién cuando haya ventas.

### 1.3 Chrome Web Store (complemento)
- **Costo:** US$5 una sola vez. Cuenta con verificación en dos pasos, el email no se puede cambiar después (usar uno dedicado), máximo 20 extensiones.
- **Reglas que importan:** Manifest V3 (prohíbe cargar código remoto), **un solo propósito por extensión**, justificar por escrito cada permiso, declarar qué datos se recolectan, **política de privacidad pública obligatoria** si se maneja información del usuario. Para operar en la UE hay que declararse "comerciante" y publicar dirección y teléfono.
- **Revisión:** normalmente unos días, puede llevar semanas, y **cada actualización vuelve a revisión**. Pedir acceso a todos los sitios (`<all_urls>`) es lo que más escrutinio genera; una extensión de dictado lo necesita.
- **Límites técnicos (de la documentación oficial de Chrome):**
  - Los atajos que funcionan con Chrome en segundo plano ("globales") **solo pueden ser Ctrl+Shift+[0–9]**. No hay Win+Espacio ni Bloq Mayús.
  - Los atajos deben llevar Ctrl o Alt, y Ctrl+Alt no está permitido.
  - **Solo escribe dentro de Chrome**: no llega a Cursor, VS Code, WhatsApp Desktop, Word ni Slack de escritorio.
  - El micrófono se usa desde un "documento offscreen" sin límite de duración, pero hay que obtener el permiso del usuario desde una página visible de la extensión (probarlo en la práctica).
- **Uso correcto:** versión "WhisperPRO Lite" con cupo chico, que dicta en Gmail, Docs, ChatGPT o Claude web e invita a instalar la app. La Chrome Web Store tiene búsqueda propia con tráfico: es un canal para conseguir usuarios.

### 1.4 Otros canales gratis
- **winget** (el gestor de paquetes de Windows): se publica con un manifiesto en un repositorio público; ideal para desarrolladores. Conviene tener el instalador firmado.
- **Mac App Store**, cuando haya versión Mac: cuenta de Apple US$99/año.

---

## 2. Cómo funcionan las apps de este rubro
Todas siguen el mismo circuito, y el nuestro ya lo tiene completo:
1. **Atajo global** del sistema operativo (no del navegador) que arranca la grabación.
2. **Captura de audio** del micrófono, en bloques de pocos milisegundos.
3. **Transcripción en la nube** (Whisper u otro modelo propio). Wispr acaba de presentar Canto, su modelo propio para ambientes con ruido.
4. **Limpieza con un modelo de lenguaje**: puntuación, muletillas, formato y, en las mejores, contexto (en qué app estás, nombres de contactos, términos técnicos).
5. **Inyección del texto** en la app activa: pegar con el portapapeles o simular teclas.
6. **Historial**, diccionario personal y snippets.

La diferencia entre productos no está en el circuito (es casi un commodity) sino en tres cosas: **qué tan poco hay que corregir lo que sale**, **qué tan rápido aparece** y **qué tan liviano es en la máquina**. La métrica central de Wispr es justamente si el usuario puede mandar el texto sin editarlo.

---

## 3. Quién lidera hoy: Wispr Flow
- **Valuación US$2.000 M** con una Serie B de US$280 M (agosto 2026); US$361 M recaudados en total. Ingresos creciendo más de 150 % por trimestre.
- **Millones de usuarios**, 125.000+ empresas y 270+ de la lista Fortune 500, con ventas a empresas casi sin vendedores (todo entrante).
- **Plataformas:** Mac (oct. 2024), Windows (mar. 2025), iPhone (jun. 2025), Android.
- **Precios:** gratis 2.000 palabras por semana; Pro US$15/mes o US$12/mes anual; Teams US$12 por usuario. **India: ₹320/mes (US$3,40)**.
- **Cómo crece:** el producto se recomienda solo (retención del 70–80 % al año y 19 % de conversión de gratis a pago, según el fundador), referidos con un mes gratis, apoyo de figuras como Reid Hoffman, Marc Andreessen y Steve Wozniak, y contenido del fundador en X y LinkedIn.
- **Sus puntos débiles:** en Windows los usuarios reportan alto consumo de memoria y procesador, y cuelgues que traban la app donde dictás. Polémica de privacidad a principios de 2026 (capturas de pantalla). Trustpilot 2,7/5. Sin modo sin conexión. Precio alto para Latinoamérica. Interfaz y soporte en inglés.
- **El resto del rubro:** Superwhisper (Mac), Willow, Aqua Voice (Y Combinator), Typeless, Monologue, y del lado de pago único y código abierto VoiceInk, VoiceTypr y Handy. En extensiones de Chrome: Voice In, Voicy (US$8,49/mes) y Speechnotes. Microsoft trae dictado gratis integrado en Windows con **Win + H**.

---

## 4. Nuestra ventaja y lo que haría que nos elijan
Primero la honestidad: cualquier función que inventemos, Wispr la puede copiar en semanas. Lo que no se copia rápido es **a quién le hablás y cómo llegás**. La estrategia es ser la respuesta obvia para un segmento concreto antes de que ellos se fijen en él.

### 4.1 Lo que ya tenemos y ellos no
- **Entiende cuando cambiás de idea.** "Un velero… no, mejor no, borrá eso, hagamos un avión" queda en "hagamos un avión". Wispr edita texto con comandos explícitos; nosotros entendemos el arrepentimiento natural del que piensa en voz alta.
- **Nada se pierde.** Lo descartado queda guardado y se recupera con un clic; Win + Z cambia el resultado por lo literal. Es la red de seguridad que hace que te animes a hablar sin pensar.
- **Memoria de voz y portapapeles integrado.** Historial con búsqueda, y lo que tenías copiado antes de dictar no se pierde.
- **Esc para arrepentirse.** Confirmación antes de borrar.

### 4.2 Lo que tenemos que construir para que la elección sea obvia
1. **Español de verdad, de todas las regiones.** Argentina, el resto de LATAM y España: interfaz y soporte en español, y una IA que respeta tu variante (vos, tú, usted, vosotros), tus muletillas y tu vocabulario local sin "neutralizarlos". (Corregido 12/10: el producto no se enfoca en un solo acento.) Wispr hizo esto en India y se volvió su segundo mercado: es la prueba de que el camino funciona.
2. **Precio latinoamericano y pago local.** Pesos con Mercado Pago, reales con Pix, US$8 para el resto. Con la Store se cobra por fuera sin comisión.
3. **Liviano en Windows.** Medirlo y publicarlo: "usa X MB de memoria en reposo". Es la queja número uno contra el líder.
4. **Privacidad como promesa escrita.** Sin capturas de pantalla, sin guardar audio, historial solo en tu computadora. Es exactamente donde el líder perdió confianza este año.
5. **Aliado del que trabaja con IA.** Dictarle a Cursor, Claude o ChatGPT es el uso que más crece: modo "prompt" que estructura lo que dijiste como pedido claro, y abrir links que dictaste o seleccionaste (pendiente anotado).
6. **Distribución que ellos no tienen:** la Microsoft Store en español, festudios y sus clientes, la comunidad de desarrolladores hispanos, y contenido de Juan en redes con el demo del velero.

### 4.3 Riesgo a vigilar
- **Win + H es el dictado nativo de Windows.** Hoy usamos Win + H para el historial y lo pisamos. Hay que moverlo (por ejemplo, Win + Alt + H) para no romper una función del sistema.
- **Dependencia de Groq.** Ya mitigada con descubrimiento automático de modelos y respaldo en OpenAI y Gemini; en producto, las llamadas deben pasar por nuestro servidor.

---

## 5. Próximos pasos propuestos
1. Terminar la validación del overlay y generar el `.exe` v6.9+.
2. Mover el historial de Win + H a otro atajo.
3. **Microsoft Store:** abrir la cuenta (gratis), empaquetar en MSIX y subir una beta. Resuelve la firma sin pagar certificado.
4. Página de privacidad pública en festudios.pro (la exigen las dos tiendas).
5. Extensión "Lite" de Chrome **después** de la Store, como canal de captación.
6. Backend con login y cupo de palabras para cobrar (el plan del 11/10 sigue vigente).

---

### Fuentes
- [Publicar extensiones de Chrome: requisitos y costos (jul. 2026)](https://pearpages.com/blog/2026/07/19/publishing-chrome-extensions-what-it-takes-what-it-costs)
- [chrome.commands — atajos globales (documentación oficial)](https://developer.chrome.com/docs/extensions/reference/api/commands)
- [chrome.offscreen — documentos offscreen (documentación oficial)](https://developer.chrome.com/docs/extensions/reference/api/offscreen)
- [Extensiones de dictado para Chrome 2026 (Voicy)](https://usevoicy.com/blog/voice-to-text-chrome-extensions/)
- [Publicar tu primera app de Windows (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app)
- [Opciones de firma de código para Windows (Microsoft Learn, act. 29/08/2026)](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- [Microsoft elimina la tarifa de la Store para desarrolladores individuales (2025)](https://alternativeto.net/news/2025/9/microsoft-finally-drops-microsoft-store-publishing-fee-for-individual-developers-globally)
- [Apps que no son juegos se quedan con el 100 % usando pagos propios (PC Gamer, 2021)](https://www.pcgamer.com/au/windows-store-devs-can-keep-100-of-their-revenue-unless-theyre-making-games)
- [Wispr levanta US$280 M a US$2.000 M (Pulse 2.0, ago. 2026)](https://pulse2.com/wispr-raises-280-million-at-2-billion-valuation-as-revenue-grows-150-quarterly-and-voice-ai-push-accelerates)
- [Cómo crece Wispr Flow (Postbeam, cifras del fundador y de terceros)](https://www.postbeam.ai/blog/how-wisprflow-grows)
- [Precios de Wispr Flow (eesel, 2026)](https://www.eesel.ai/blog/wispr-flow-pricing)
- [Apps de dictado con IA 2026 (AI Chat Daily)](https://www.aichatdaily.com/ai-tools/best-ai-dictation-apps-2026-ranked)

## Anexo (12/10): sacar la fricción de la API key
> DECISIÓN de Juan (12/10): se queda la clave propia de cada usuario, con conexión guiada (la app detecta la clave al copiarla). El servidor propio de abajo queda como opción futura para un plan Pro.
- Hoy cada instalación necesita su propia key de Groq. Para un producto comercial eso no va: el usuario no debería ver la palabra "API".
- **Solución recomendada: servidor intermedio (proxy) de FESTUDIOS.** La app manda el audio a nuestro servidor (Supabase Edge Function o Cloudflare Worker), el servidor lo reenvía a Groq con NUESTRA key y devuelve el texto. La key nunca sale del servidor.
- El usuario solo se registra con email (o Google) desde el panel; la app guarda un token. El servidor cuenta minutos/palabras por usuario y corta al pasar el límite del plan gratis.
- **Nunca** meter nuestra key adentro del .exe: se extrae en minutos y nos vacían la cuenta.
- Costo aproximado: Whisper large-v3-turbo en Groq ronda US$0,04 por hora de audio (verificar en groq.com/pricing antes de fijar precios). Un usuario gratis con ~3.000 palabras/semana (~20 min de audio) cuesta centavos por mes; la corrección con LLM agrega muy poco.
- Hay que pasar Groq a plan pago (Developer): el plan gratis tiene límites por organización (20 pedidos/min, 7.200 s de audio/hora) que se agotan con pocos usuarios simultáneos.
- "Traé tu propia clave" queda como opción avanzada (gratis ilimitado para quien la tenga), no como paso del instalador.
- Orden: (1) Edge Function `transcribir` + `corregir` en Supabase con límite por usuario; (2) login por email en el panel; (3) el instalador ya no pide key; (4) planes y cobro (Mercado Pago / Stripe / Microsoft Store).
