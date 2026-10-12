# WhisperPRO — Plan de producto y negocio
> Escrito 11/10/2026. Estado del prototipo: v5.1 funcionando como script Python en Windows (texto en vivo, corrección por IA, historial, portapapeles). Este documento es la hoja de ruta para convertirlo en producto descargable con plan gratis y pagos.

## 1. Qué aprendimos del mercado (investigado 11/10/2026)

La dictación con IA dejó de ser nicho. Wispr Flow, el líder, cerró en agosto de 2026 una Serie B de US$280 M a una valuación de US$2.000 M, con ingresos creciendo más de 150 % por trimestre, millones de usuarios y más de 125.000 empresas. Eso confirma dos cosas: la gente paga por esto, y el espacio tiene capital suficiente como para que un clon genérico no gane.

Precios de referencia de la categoría (todos en dólares, por usuario):

| Producto | Gratis | Pago | Plataformas | Lo que lo distingue |
|---|---|---|---|---|
| Wispr Flow | 2.000 palabras/semana (desktop) | 15/mes o 12/mes anual (144/año) | Mac, Win, iOS, Android | Integración con Cursor, Command Mode (editar texto seleccionado por voz), equipos |
| Willow | 2.000 palabras/mes | desde 15/mes | Desktop | Transcripciones locales, expande pocas palabras en un párrafo |
| Typeless | 4.000 palabras/semana | 12/mes anual | — | Cuota gratis generosa |
| Aqua Voice | 1.000 palabras/mes | 8/mes anual | Win, Mac | Latencia muy baja, respaldado por Y Combinator |
| Monologue | 1.000 palabras/mes | 10/mes o 100/año | — | Modelo descargable al equipo, teclado físico Monokey |
| Superwhisper | básico gratis, 15 min de prueba Pro | 8,49/mes, 84,99/año o 249,99 de por vida | Mac (Win en beta) | Varios motores, traé tu propia API key, sin límites |
| VoiceInk | — | 25 / 39 / 49 una sola vez (por dispositivo) | Mac | Lee el contexto en pantalla, formato por app o por URL, open source |
| VoiceTypr | — | 35 / 56 / 98 una sola vez | Mac, Win | Offline, 99 idiomas, open source |
| Handy | gratis y open source | — | Mac, Win, Linux | Push-to-talk mínimo |

Patrones claros del mercado:

1. El precio ancla está en **US$12–15/mes** para ilimitado, con un gratis de **1.000–4.000 palabras** que se agota rápido a propósito.
2. Hay una segunda liga de **pago único (US$25–50)** y open source que atrae a quien no quiere otra suscripción.
3. **Windows está mal atendido.** Los reviews de Wispr en Windows hablan de consumo alto de RAM y CPU en reposo, ventiladores y cuelgues que trabán también la app donde dictás. Casi todos los competidores nacieron en Mac.
4. Nadie está construido para **hispanohablantes**: la interfaz, el soporte, la facturación local (pesos, Mercado Pago) y la comprensión de muletillas y correcciones en español rioplatense son todas oportunidades vacías.
5. La **confianza** es un flanco abierto: Wispr tuvo una polémica a principios de 2026 por capturas de pantalla y opt-in de entrenamiento; Trustpilot lo tiene en 2,7/5.
6. Ninguno de los grandes hace lo que ya hace nuestro prototipo: **interpretar correcciones habladas** ("no, mejor no, borrá eso, hagamos un avión") y guardar lo descartado para recuperarlo. Willow expande, Wispr edita texto seleccionado por comando explícito, pero nadie entiende el "cambio de idea" natural del que piensa en voz alta.

## 2. Posicionamiento: el aliado del que piensa en voz alta

No vendemos "dictado". Vendemos **pensar en voz alta y que quede bien escrito**: para desarrolladores que le hablan a Cursor/Claude/ChatGPT, para dueños de negocio que responden WhatsApp todo el día, para cualquiera que escribe más lento de lo que piensa. En español primero, en inglés y portugués también.

Tres promesas que ningún competidor hace juntas:

- **Entiende cuando te corregís.** Decís "tengo una idea para un velero… no, mejor no, borrá eso, vamos a hacer un avión" y queda solo lo del avión. Y lo que descartaste no se pierde: está en el historial por si te arrepentís.
- **Liviano de verdad en Windows.** Sin Electron, sin consumo en reposo, sin trabar la app donde escribís. Esta es la queja número uno del líder y nuestra ventaja técnica más fácil de defender.
- **Tu memoria de voz.** Historial completo, portapapeles integrado (cada dictado queda copiado, y lo que tenías antes se guarda), búsqueda. Lo que dijiste hace tres días se encuentra.

Nombre: "WhisperPRO" sirve como nombre interno. Para lanzar conviene un nombre propio (Whisper es la marca del modelo de OpenAI y los dominios buenos están tomados). Candidatos a verificar: **Hablalo**, **Dictá**, **Voz.app**, **Dilo**. Decisión pendiente de Juan.

## 3. Forma del producto: app de escritorio, no extensión de Chrome

Lo evaluamos y la extensión de Chrome **no sirve como producto principal**: solo funciona dentro del navegador (nada de Cursor, VS Code, WhatsApp Desktop, Word, Slack), no puede registrar atajos globales como Bloq Mayús, y el acceso al micrófono es por pestaña. Sí sirve como **canal de adquisición** más adelante (Chrome Web Store tiene tráfico orgánico), con una versión limitada que invite a bajar la app.

Entonces: **app de escritorio para Windows primero** (donde está el hueco), Mac después, móvil (teclado) en una fase posterior.

Stack recomendado para la versión producto, en dos etapas:

- **Etapa A (semanas 1–3): empaquetar lo que ya existe.** El prototipo Python se compila con PyInstaller a un único `.exe` con instalador (Inno Setup), ícono en la bandeja del sistema, arranque con Windows, auto-actualización simple (chequeo de versión contra un JSON en nuestro servidor). Las API keys dejan de estar en un `.env`: el usuario inicia sesión y nuestro backend hace las llamadas a Groq/OpenAI con nuestras keys. Esto permite medir uso, cobrar y cambiar de proveedor sin tocar al cliente. Peso estimado del instalador: 40–60 MB. Suficiente para lanzar y validar.
- **Etapa B (meses 2–4): reescribir el cliente en Tauri (Rust + web UI).** Es lo que usan Handy y VoiceTypr; da ejecutables de ~10 MB, consumo mínimo en reposo, overlay con transparencia real y blur, y el mismo código para Windows y Mac. Se hace solo si la etapa A demuestra tracción.

## 4. Funcionalidades por versión

**v1.0 (lanzamiento gratis + Pro)**
- Push-to-talk configurable (Bloq Mayús + Espacio por defecto) y modo toggle.
- Texto en vivo en cualquier input mientras hablás.
- Corrección inteligente de autocorrecciones habladas; opción "literal" para desactivarla.
- Historial con búsqueda, mensaje completo, lo descartado, y portapapeles integrado.
- Overlay rediseñado (el actual) con tema claro/oscuro.
- Idiomas: español, inglés, portugués con detección automática; 50+ idiomas vía Whisper.
- Diccionario personal (nombres propios, términos técnicos, marcas) que se inyecta al modelo.
- Snippets por voz: "firma" → pega tu firma; "mi mail" → tu correo.

**v1.1–1.3 (primeros 90 días, según lo que pida la gente)**
- Modos por aplicación: tono informal en WhatsApp, técnico y con bloques de código en Cursor/VS Code, formal en Gmail. Se detecta la ventana activa.
- Comandos de edición sobre texto seleccionado ("hacelo más corto", "pasalo a inglés", "ponelo en lista").
- Modo "pregunta rápida": Bloq Mayús + Q, hacés una pregunta en voz alta y la respuesta aparece en el overlay (sin abrir ChatGPT).
- Notas de voz largas (reuniones de hasta 2 h) con resumen y puntos de acción, guardadas en el historial.

**v2 (meses 4–8)**
- Mac.
- Modo offline con Whisper local para plan Pro (privacidad total, sin internet).
- Equipos: diccionario compartido, facturación centralizada, panel de uso.
- Teclado móvil (iOS/Android) sincronizado con el historial.

## 5. Modelo de negocio y precios

Cobramos en dólares vía Stripe/Paddle para el mundo y en pesos vía Mercado Pago para Argentina (y después Brasil con Pix vía Mercado Pago). Paddle resuelve impuestos internacionales como merchant of record; es la opción recomendada para el exterior.

| Plan | Precio | Qué incluye | Para quién |
|---|---|---|---|
| **Gratis** | 0 | 3.000 palabras/semana (más que Wispr), corrección inteligente, historial 7 días, 1 dispositivo | Probar y engancharse. Marca de agua: ninguna; el límite se siente a la semana de uso real |
| **Pro** | US$8/mes o US$72/año (6/mes) · Argentina: $9.900/mes | Ilimitado, historial completo con búsqueda, modos por app, snippets, diccionario, portapapeles ilimitado, 3 dispositivos | Desarrolladores, freelancers, dueños de negocio |
| **Pro de por vida** | US$79 una sola vez (primeros 500 compradores: US$49) | Todo Pro para siempre, actualizaciones 2 años | El que odia suscripciones; financia los primeros meses |
| **Equipo** | US$12/usuario/mes | Pro + diccionario compartido, facturación central, panel, soporte prioritario | Estudios, agencias, equipos de soporte |

Por qué US$8 y no 15: entramos por debajo del líder con un producto que hace algo que él no hace, en un mercado (hispanohablante, Windows) donde el precio de 15 dólares es un freno real. El precio sube a US$10–12 cuando tengamos 500 pagos y reseñas.

Costo variable estimado por usuario Pro activo: Groq cobra ~US$0,04 por hora de audio con whisper-large-v3-turbo y centavos por las llamadas a Llama 3.3. Un usuario intenso (1 hora de dictado por día) cuesta menos de US$1,50/mes. Margen bruto superior al 80 % incluso con usuarios pesados; el gratis con 3.000 palabras/semana cuesta centavos.

Proyección conservadora (para tener un número, no una promesa): 10.000 descargas en 6 meses, 4 % de conversión a Pro = 400 pagos × US$7 promedio = US$2.800/mes recurrentes, más ventas de por vida. Con 3.000 pagos (meta a 18 meses) son US$20.000/mes.

## 6. Cómo lo vamos a vender

1. **Build in public en español.** El contenido del Motor de contenido IG de festudios ya existe; WhisperPRO es la historia perfecta: "estoy construyendo la herramienta de dictado que Windows no tiene". Videos cortos mostrando el "no, mejor no, borrá eso" funcionando. Ese demo es el gancho: nadie más lo tiene.
2. **Product Hunt + Hacker News + r/cursor, r/ClaudeAI, r/windows.** La narrativa "liviano en Windows, entiende cuando te corregís, 8 dólares" está hecha para esas comunidades.
3. **Comunidades de desarrolladores hispanos**: Midudev, Discord de Platzi, Twitter dev en español. Programa de afiliados con 30 % recurrente el primer año.
4. **Chrome Web Store** con una versión "lite" (dictado en el navegador, 1.000 palabras/semana) que redirige a la app: tráfico orgánico gratis.
5. **Clientes de festudios** como primeros usuarios Pro y testimonios reales: Tco Burgers respondiendo pedidos por voz, Polo contestando consultas.
6. **SEO de comparación**: páginas "alternativa a Wispr Flow en español", "Wispr Flow para Windows lento" — es exactamente lo que hacen todos los competidores chicos y funciona (las fuentes de esta investigación son casi todas ese tipo de página).

## 7. Riesgos y cómo los manejamos

- **Dependencia de Groq.** Si cambia precios o límites, el backend ya abstrae el proveedor: OpenAI, Deepgram y Whisper local son reemplazos en días. El plan de por vida se limita a 2 años de actualizaciones por esto.
- **Nombre y marca.** No lanzar con "Whisper" en el nombre.
- **Privacidad.** Decirlo claro desde el día uno: no entrenamos con tu audio, no guardamos audio, el historial es local y se puede borrar. Es el flanco donde el líder sangra.
- **Soporte.** Un solo fundador: documentación muy buena, FAQ en la app, y soporte por mail/WhatsApp con respuesta en 24 h (ya es el estándar de festudios).
- **Windows Defender / SmartScreen** marca ejecutables nuevos como desconocidos. Firmar el instalador con certificado (US$200–400/año) antes de lanzar públicamente.

## 8. Plan de ejecución (próximas 6 semanas)

| Semana | Entregable | Responsable |
|---|---|---|
| 1 | Prototipo validado en la PC de Juan (atajo, texto en vivo, corrección). Elegir nombre y registrar dominio. | Claude + Juan |
| 1–2 | Backend mínimo (Supabase: usuarios, plan, contador de palabras, proxy a Groq). Login en la app. | Claude |
| 2–3 | Empaquetado `.exe` + instalador, bandeja del sistema, arranque con Windows, auto-update. | Claude (build en la PC de Juan) |
| 3 | Landing con demo en video, lista de espera, precios. Mercado Pago + Paddle. | Claude + Juan (cuentas) |
| 4 | Beta cerrada: 20 usuarios (clientes festudios + comunidad). Medir: dictados/día, retención a 7 días, errores. | Juan recluta |
| 5 | Diccionario, snippets, modos por app según feedback. Firma de código. | Claude |
| 6 | Lanzamiento público: Product Hunt, IG, comunidades. Precio de lanzamiento de por vida US$49. | Juan + Claude |

## 9. Decisiones tomadas hoy (11/10/2026)

- App de escritorio Windows primero; extensión de Chrome solo como canal lite más adelante. Motivo: la extensión no puede hacer atajos globales ni escribir en otras apps.
- Etapa A con Python empaquetado para validar rápido; Tauri recién con tracción. Motivo: no invertir dos meses de reescritura antes de saber si la gente paga.
- Precio Pro de entrada US$8/mes, por debajo del líder. Motivo: mercado hispano + Windows, y entrar a ganar reseñas.
- Las keys de IA pasan al backend (el usuario no configura nada). Motivo: cobrar, medir y cambiar de proveedor sin tocar al cliente.
