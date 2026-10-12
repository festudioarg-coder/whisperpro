# WhisperPRO — Qué le duele al usuario, qué motor usar y qué aportamos
> 12/10/2026. Público: hispanohablantes de **Argentina, el resto de LATAM y España** (todos los acentos), más inglés. Nada de enfocarse en un solo acento.
> Fuentes: comentarios de Hacker News 2025–2026, Trustpilot, foros de los fabricantes y blogs de competidores (marcados [sesgo], porque tienen interés comercial). Reddit no se pudo leer directamente. La frecuencia de cada queja es una estimación.

## 1. Las quejas que más se repiten
| # | Queja | Ejemplo | Cuánto aparece |
|---|---|---|---|
| 1 | Precio y suscripción | "tired of paying $15/mo for Wispr Flow" (HN) | Muy seguido |
| 2 | Privacidad: audio y pantalla que van a la nube | "your entire page contents get streamed to their server" (HN) | Seguido |
| 3 | En Windows, peores versiones y mucho consumo de RAM y CPU | Wispr ~800 MB de RAM sin hacer nada [sesgo] | Seguido |
| 4 | Acentos, español y mezcla de idiomas | Superwhisper "German dictation translated to English" (su foro) | Seguido entre no angloparlantes |
| 5 | Caídas y empeoramiento de la calidad | error de Wispr de 9,0% a 11,2% en un mes (HN) | Bastante |
| 6 | El texto no llega a la app (Citrix/RDP, letras duplicadas, VS Code congelado) | "simply don't work" en RDP (HN) | Bastante |
| 7 | Win+H de Windows se corta solo en los silencios y la puntuación sale mal | se apaga a los 5–10 s [sesgo] | Bastante |
| 8 | Frases inventadas en silencios ("Gracias por ver", "Subtítulos de Amara") | Foro de OpenAI | Bastante |
| 9 | Nombres propios y jerga técnica | piden "custom vocabulary" (HN) | Bastante |
| 10 | Latencia | "the full loop has to feel instant" (HN) | Bastante |
| 11 | Dragon: soporte malo, licencias, incompatible con Windows 11 | 1,6/5 en Trustpilot | Muy seguido, solo en Dragon |

**Lectura:** la gente se va de Wispr y Superwhisper por precio y privacidad. El hispanohablante con Windows está mal atendido. Lo que más pesa en la experiencia es lo último del recorrido: que entienda tu acento, que no traduzca y que el texto llegue bien a la app.

**Wispr Flow en Trustpilot:** su perfil fue eliminado por incumplir las directrices (captura de Juan del 12/10/2026). No se sabe el motivo exacto, así que no hay que afirmarlo en público. Lección: ver `REGLAS-DE-CONFIANZA.md`.

## 2. ¿Algo mejor que Whisper?
Aviso: no existe un ranking independiente de español por acento. El ranking de Artificial Analysis mezcla audios y no separa por idioma. **Hay que probar con audios nuestros:** grabar 10 frases por acento (AR, MX, CO, ES) y medir con Soniox Compare, que es gratis y de código abierto.

| Motor | Error (lote) | Resultados mientras hablás | Precio/hora | Gratis para el usuario |
|---|---|---|---|---|
| **Groq whisper-large-v3** | menos que turbo | No | $0,111 | **Sí, los mismos límites que turbo** |
| Groq whisper-large-v3-turbo (lo que usábamos) | 4,6% | No | $0,04 | Sí |
| **Deepgram Nova-3 Multilingual** | 5,2% | **Sí (~60 ms)** y mezcla ES/EN | ~$0,35 | **$200 de crédito** (~575 h) |
| AssemblyAI Universal-Streaming | 3,8% | Sí | $0,15 | $50 sin tarjeta |
| ElevenLabs Scribe v2 Realtime | 2,2% / 3,6% en tiempo real | Sí (~150 ms) | $0,39 | Plan gratis chico ⚠️ |
| Microsoft MAI-Transcribe-2 (sept. 2026) | 2,0% | ⚠️ | $0,10 | Requiere Azure |
| Mistral Voxtral | 3,6% | Sí | $0,36 | Modelo abierto |
| NVIDIA Parakeet v3 (en la PC) | 4,5% (español 3,45% en FLEURS) | En la PC | $0 | Sí, sin internet |
| Gemini 3 Flash | 2,9% | API aparte | Por uso | ⚠️ En el plan gratis, Google puede usar tu audio para entrenar |

### Qué hacemos
1. **Hecho (v6.14):** pasamos a **whisper-large-v3** como motor principal: comete menos errores en español y en el plan gratis no cuesta más. Turbo queda de respaldo.
2. **Próximo:** opción **"motor en tiempo real"** con Deepgram Nova-3. El usuario trae su clave con $200 gratis. Muestra el texto mientras hablás de verdad, sin esperar la pausa, y mezcla español e inglés.
3. **Después:** **modo sin internet** con Parakeet v3 o whisper.cpp, para privacidad total y para cuando se cae la API.
4. **Para probar:** ElevenLabs Scribe y MAI-Transcribe-2 como "calidad máxima", si en nuestras pruebas rinden con acentos latinos.
- ⚠️ El límite de Groq es de 20 pedidos por minuto. Con cortes en cada pausa, alguien que hace muchas pausas podría llegar al tope. Hay que medirlo y juntar fragmentos de al menos 3 s.

## 3. Qué aportamos (ordenado por impacto y esfuerzo)
| # | Mejora | Resuelve | Impacto | Esfuerzo | Estado |
|---|---|---|---|---|---|
| 1 | **Nunca perdés texto:** audio y texto guardados antes de enviar, reintentos, siempre al portapapeles con aviso y historial recuperable | 5, 6 | Alto | Bajo | En parte (historial + portapapeles + tilde "Copiado") |
| 2 | **No inventa en silencios:** detector de voz + filtro de frases fantasma | 8 | Alto | Bajo | Hecho (v6.8–6.11) |
| 3 | **Respeta tu español:** no cambia vos/tú/usted/vosotros ni el vocabulario local; entiende correcciones de cualquier región | 4 | Alto, nadie lo hace | Bajo | **Hecho (v6.14)** |
| 4 | **Idioma fijo o mezcla ES/EN elegida**, en lugar de detección automática que termina traduciendo | 4 | Alto | Bajo | Pendiente |
| 5 | **Glosario personal:** nombres, marcas y jerga en el prompt + aprende de tus correcciones | 9 | Alto | Bajo-medio | Pendiente |
| 6 | **Privacidad como bandera:** tu clave, sin servidor nuestro, sin capturar pantalla, historial local | 2 | Alto | Bajo | Hecho; falta comunicarlo |
| 7 | **Escritura robusta:** modo teclado para RDP/Citrix, sin letras duplicadas, estrategia por app | 6 | Alto | Medio | Pendiente |
| 8 | **Modos por app:** chat informal, mail formal, código sin reescribir | — | Medio-alto | Medio | Pendiente |
| 9 | **Comandos de voz:** "nuevo párrafo", "en viñetas", "borrá la última frase" | — | Medio | Medio | En parte (autocorrecciones) |
| 10 | **Liviana:** menos de 100 MB de RAM en reposo, medido y publicado | 3 | Medio | Depende | Medir |
| 11 | **Tiempo real** (Deepgram) | 10 | Medio-alto | Medio-alto | Pendiente |
| 12 | **Sin internet** (Parakeet/whisper.cpp) | 2, 5 | Medio | Alto | Pendiente |
| 13 | **Atajo configurable** que avisa si choca con otro (Win+Espacio choca con el cambio de idioma de teclado de Windows; Win+H con el dictado nativo) | — | Medio | Bajo | Pendiente |

## Fuentes
- HN: [precio](https://news.ycombinator.com/item?id=47119223), [Wispr vs iOS](https://news.ycombinator.com/item?id=48198223), [privacidad](https://news.ycombinator.com/item?id=48577831), [contexto en la nube](https://news.ycombinator.com/item?id=48531184), [recursos](https://news.ycombinator.com/item?id=48193904), [acento](https://news.ycombinator.com/item?id=48092293), [error en aumento](https://news.ycombinator.com/item?id=48548002), [RDP](https://news.ycombinator.com/item?id=46720497), [letras duplicadas](https://news.ycombinator.com/item?id=48896955), [continuo](https://news.ycombinator.com/item?id=48965889), [atajos](https://news.ycombinator.com/item?id=49815368)
- [Superwhisper: foro](https://superwhisper.userjot.com/board/p/automatic-language-detection-always-translates-to-english) · [Superwhisper: documentación](https://superwhisper.com/docs/common-issues/language-detection)
- [Voibe: alternativas para Windows](https://www.getvoibe.com/resources/best-wispr-flow-alternatives-windows/) · [Trustpilot: Nuance](https://nz.trustpilot.com/review/www.nuance.com) · [Trustpilot: Wispr](https://es.trustpilot.com/review/wisprflow.ai)
- [ElevenForum: Win+H](https://www.elevenforum.com/t/voice-typing-problem-with-punctuation.35104/latest) · [Foro de OpenAI: alucinaciones](https://community.openai.com/t/whisper-api-hallucinating-on-empty-sections/93646)
- [Artificial Analysis STT](https://artificialanalysis.ai/speech-to-text) · [Soniox Compare](https://soniox.com/compare) · [Groq STT](https://console.groq.com/docs/speech-to-text) · [Groq límites](https://console.groq.com/docs/rate-limits) · [Deepgram precios](https://deepgram.com/pricing) · [Deepgram mezcla de idiomas](https://developers.deepgram.com/docs/multilingual-code-switching) · [AssemblyAI precios](https://www.assemblyai.com/pricing.md) · [ElevenLabs STT](https://elevenlabs.io/docs/capabilities/speech-to-text) · [Mistral Voxtral](https://mistral.ai/news/voxtral-transcribe-2) · [MAI-Transcribe-2](https://microsoft.ai/news/mai-transcribe-2) · [Parakeet v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)
