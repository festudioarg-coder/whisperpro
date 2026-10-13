"""Genera las páginas legales de la landing con un mismo estilo y un mismo pie.

Uso (desde la raíz del repo):   python landing/generar_legales.py
Escribe: privacidad/ terminos/ contacto/ baja-y-arrepentimiento/ licencias/ (index.html cada una) y sitemap.xml

IMPORTANTE: son borradores redactados para ser ciertos hoy (lo que el código realmente hace) y para cumplir lo que
piden la Microsoft Store, Google y la normativa argentina de consumo y datos. Antes de publicar conviene que los
revise un profesional matriculado en Argentina y que se completen los datos marcados entre corchetes.
"""
import json
import os
import re

RAIZ = os.path.dirname(os.path.abspath(__file__))
FECHA = "12 de octubre de 2026"
FECHA_ISO = "2026-10-12"
VERSION = "v1.0"
MAIL = "festudioarg@gmail.com"
EMISOR = "FESTUDIO ARGENTINA"
BASE = "https://festudios.pro/whisperpro/"
DEFENSA = "https://www.argentina.gob.ar/produccion/defensadelconsumidor"

PAGINAS = [  # ruta, título del menú
    ("privacidad", "Privacidad"),
    ("terminos", "Términos y condiciones"),
    ("baja-y-arrepentimiento", "Cancelar o arrepentirte"),
    ("contacto", "Contacto"),
    ("licencias", "Licencias"),
]
EXTRA = ("descargar", "pro")   # páginas que no van en el pie legal

CSS = """
@font-face{font-family:'WP Sans';src:url('fonts/Bricolage.woff2') format('woff2');font-weight:200 800;font-stretch:75% 100%;font-display:swap}
@font-face{font-family:'WP Mono';src:url('fonts/MartianMono.woff2') format('woff2');font-weight:100 800;font-stretch:75% 112%;font-display:swap}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#0a0b10;color:#c9ccd8;font-family:'WP Sans',system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.7;font-size:18px}
a{color:#c084fc}a:focus-visible{outline:2px solid #7aa2ff;outline-offset:3px;border-radius:6px}
.wrap{max-width:800px;margin:0 auto;padding:36px 24px 96px}
.top{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:48px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:11px;text-decoration:none;color:#e9eaf2;font-size:20px;font-weight:600;font-stretch:84%;letter-spacing:-.03em}
.brand img{width:32px;height:32px;border-radius:9px}.brand b{font-weight:800;color:#c084fc}
.mono{font-family:'WP Mono',monospace;font-stretch:86%;font-size:12px;color:#8b92a8;letter-spacing:.04em}
.mono a{color:#8b92a8;text-decoration:none}.mono a:hover{color:#e9eaf2}
h1{margin:0 0 8px;font-size:clamp(34px,6vw,54px);line-height:1.04;letter-spacing:-.04em;color:#fff;font-variation-settings:"opsz" 72}
h2{margin:46px 0 10px;font-size:25px;letter-spacing:-.02em;color:#fff;line-height:1.2}
h3{margin:26px 0 6px;font-size:19px;color:#e9eaf2}
p{margin:12px 0}ul,ol{padding-left:22px}li{margin:7px 0}
.box{background:#11131a;border:1px solid #1b1e29;border-radius:18px;padding:22px 26px;margin:22px 0}
.ok{color:#34e0a1}.out{color:#c084fc}
.toc{columns:2;column-gap:32px;font-size:15.5px;padding-left:20px}
.pend{background:rgba(255,193,7,.10);border-radius:4px;padding:0 4px}
table{width:100%;border-collapse:collapse;font-size:15.5px;margin:18px 0}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #1b1e29;vertical-align:top}th{color:#8b92a8;font:600 11px 'WP Mono';font-stretch:86%;letter-spacing:.1em;text-transform:uppercase}
.btn{display:inline-block;margin:6px 10px 6px 0;padding:14px 22px;border-radius:12px;background:linear-gradient(160deg,#9b6bff 0%,#7c3aed 45%,#4c1d95 100%);color:#fff;text-decoration:none;font-weight:800;font-size:17px}
.btn.s{background:transparent;border:1px solid #2a2e3d;color:#e9eaf2}
.exito{border:1px solid rgba(52,224,161,.45);background:linear-gradient(160deg,rgba(52,224,161,.10),rgba(52,224,161,.02));border-radius:20px;padding:30px 28px;text-align:center}
.exito .tilde{width:68px;height:68px;border-radius:50%;margin:0 auto 14px;display:grid;place-items:center;background:#34e0a1;color:#05140d;font-size:38px;font-weight:800;box-shadow:0 0 0 10px rgba(52,224,161,.14)}
.exito h2{margin:0 0 6px;font-size:28px}.exito .mail{display:inline-block;margin:6px 0 12px;padding:5px 14px;border-radius:999px;background:#0a0b10;border:1px solid #2a2e3d;color:#fff;font-size:17px;word-break:break-all}
.exito ol{text-align:left;max-width:440px;margin:14px auto 0}.exito .chico{font-size:14.5px;color:#8b92a8;margin-top:16px}
.aviso{border:1px solid rgba(251,191,36,.5);background:rgba(251,191,36,.08);border-radius:20px;padding:24px 28px;text-align:center}
.aviso h2{margin:0 0 6px;font-size:24px;color:#fbbf24}
.spin{display:inline-block;width:15px;height:15px;margin-right:9px;border:2.5px solid currentColor;border-right-color:transparent;border-radius:50%;vertical-align:-2px;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.btn:disabled{opacity:.75;cursor:progress}
@media (prefers-reduced-motion:reduce){.spin{animation-duration:3s}}
.paso{display:flex;gap:16px;margin:18px 0}.paso .n{flex:none;width:34px;height:34px;border-radius:50%;background:#7c3aed;color:#fff;font:700 16px/34px 'WP Sans',sans-serif;text-align:center}
.paso h3{margin:2px 0 4px}.paso p{margin:4px 0}
figure{margin:14px 0 6px}figure img{display:block;width:100%;height:auto;border-radius:14px;border:1px solid #1b1e29}figcaption{font-size:14px;color:#8b92a8;margin-top:8px}
.kbd{font:600 14px 'WP Mono',monospace;background:#161923;border:1px solid #262a37;border-radius:6px;padding:1px 7px;color:#e9eaf2;white-space:nowrap}
footer{border-top:1px solid #1b1e29;margin-top:72px;padding-top:28px}
footer nav{display:flex;flex-wrap:wrap;gap:10px 26px;margin-bottom:16px}footer nav a{color:#aab0c4;text-decoration:none;font-size:15px}footer nav a:hover{color:#fff}
@media (max-width:640px){.toc{columns:1}body{font-size:17px}}
a{overflow-wrap:anywhere}
@media (max-width:640px){
.wrap{padding:24px 18px 72px}.top{margin-bottom:30px}
table.resp,table.resp tbody,table.resp tr,table.resp td{display:block;width:100%}
table.resp tr.cab{display:none}
table.resp tr{border:1px solid #1b1e29;border-radius:14px;padding:8px 14px;margin:12px 0;background:#0e1016}
table.resp td{border:0;padding:6px 0}
table.resp td::before{content:attr(data-l);display:block;font:600 11px 'WP Mono',monospace;letter-spacing:.07em;color:#8b92a8;text-transform:uppercase;margin-bottom:2px}
footer nav a{display:inline-block;padding:9px 0}
.btn{display:block;width:100%;text-align:center;border:0}
}

"""


def pie(actual):
    nav = "".join(f'<a href="{r}/"{" aria-current=\"page\" style=\"color:#fff\"" if r == actual else ""}>{t}</a>' for r, t in PAGINAS)
    return f"""<footer><nav aria-label="Información legal">{nav}<a href="./">Volver a WhisperPRO</a></nav>
<p class="mono">{EMISOR} · <a href="https://festudios.pro/?utm_source=whisperpro&amp;utm_medium=legal&amp;utm_campaign=pie">festudios.pro</a> · Documento {VERSION} · Actualizado el {FECHA}</p></footer>"""


def tablas_responsivas(html):
    """En el celular, las tablas con encabezado se muestran como tarjetas (cada celda lleva su rótulo)."""
    def una(m):
        t = m.group(0)
        filas = re.findall(r'<tr>.*?</tr>', t, flags=re.S)
        heads = re.findall(r'<th>(.*?)</th>', filas[0], flags=re.S) if filas else []
        if not heads:
            return t
        def etiquetar(r):
            it = iter(heads)
            return re.sub(r'<td>', lambda _: '<td data-l="%s">' % re.sub(r'<.*?>', '', next(it, '')).replace('"', ''), r)
        for r in filas[1:]:
            t = t.replace(r, etiquetar(r), 1)
        t = t.replace(filas[0], filas[0].replace('<tr>', '<tr class="cab">', 1), 1)
        return t.replace('<table>', '<table class="resp">', 1)
    return re.sub(r'<table>.*?</table>', una, html, flags=re.S)


def pagina(ruta, titulo, descripcion, cuerpo):
    return f"""<!doctype html>
<html lang="es-AR">
<head>
<meta charset="utf-8">
<base href="/whisperpro/">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} — WhisperPRO</title>
<meta name="description" content="{descripcion}">
<link rel="canonical" href="{BASE}{ruta}/">
<meta name="robots" content="index,follow">
<link rel="icon" href="favicon.ico" sizes="any">
<style>{CSS}</style>
</head>
<body><div class="wrap">
<div class="top"><a class="brand" href="./"><img src="img/logo-64.png" alt="" width="32" height="32"><span>Whisper<b>PRO</b></span></a><span class="mono"><a href="https://festudios.pro/?utm_source=whisperpro&amp;utm_medium=legal&amp;utm_campaign=desarrollado-por">Desarrollado por FESTUDIOS</a></span></div>
<h1>{titulo}</h1>
{"" if ruta in EXTRA else f"<p class=\"mono\">Documento {VERSION} · Última actualización: {FECHA}</p>"}
{tablas_responsivas(cuerpo)}
{pie(ruta)}
</div></body></html>
"""


PRIV = f"""
<p>Esta política explica, sin vueltas, qué datos maneja WhisperPRO, dónde quedan, qué sale de tu equipo y qué derechos tenés. WhisperPRO es una aplicación de dictado por voz para Windows (y una versión web para el teléfono) ofrecida por {EMISOR} («FESTUDIOS», «nosotros»).</p>

<div class="box">
<p class="ok" style="margin:0 0 8px"><b>Queda en tu equipo</b></p>
<ul style="margin:0"><li>Tu historial de dictados y el portapapeles guardado</li><li>Tu clave de IA y tus ajustes</li><li>Las capturas de pantalla, si activás esa función</li><li>Un archivo de registro técnico (sin el contenido de lo que dictás, salvo que actives el modo de depuración)</li></ul>
<p class="out" style="margin:18px 0 8px"><b>Lo único que sale</b></p>
<ul style="margin:0"><li>Mientras dictás, el audio y su transcripción viajan directo de tu equipo al motor de IA que conectaste (por defecto, Groq), con tu propia clave</li></ul>
</div>
<p><b>FESTUDIOS no recibe tu voz, tu texto ni tu historial.</b> WhisperPRO no usa servidores nuestros para dictar. No hay cuenta de usuario, ni telemetría, ni estadísticas de uso dentro de la aplicación.</p>

<h2>Índice</h2>
<ol class="toc"><li><a href="privacidad/#responsable">Responsable</a></li><li><a href="privacidad/#datos">Qué datos se guardan en tu equipo</a></li><li><a href="privacidad/#salen">Qué sale de tu equipo</a></li><li><a href="privacidad/#finalidad">Para qué se usan y por cuánto tiempo</a></li><li><a href="privacidad/#borrar">Cómo borrar tus datos</a></li><li><a href="privacidad/#derechos">Tus derechos</a></li><li><a href="privacidad/#seguridad">Seguridad</a></li><li><a href="privacidad/#sitio">Este sitio web y cookies</a></li><li><a href="privacidad/#menores">Menores</a></li><li><a href="privacidad/#cambios">Cambios y contacto</a></li></ol>

<h2 id="responsable">1. Responsable</h2>
<p>{EMISOR} (marca «FESTUDIOS»), Argentina. Correo de contacto: <a href="mailto:{MAIL}">{MAIL}</a>. Domicilio: Independencia 3800, Olavarría, Buenos Aires. CUIT: 20-36215734-0.</p>
<p>Como la aplicación trata tus datos dentro de tu equipo y los envía directamente al proveedor de IA que elegiste, FESTUDIOS no almacena ni accede a los datos de tu uso. Solo tratamos los datos que nos enviás vos por contacto (por ejemplo, tu correo si nos escribís o te anotás en una lista de espera).</p>

<h2 id="datos">2. Qué datos se guardan en tu equipo</h2>
<table><tr><th>Dato</th><th>Dónde</th><th>Para qué</th></tr>
<tr><td>Historial de dictados: lo que dijiste (literal), lo que se escribió, lo descartado, fecha y duración</td><td>Archivo en la carpeta de datos de la app</td><td>Que puedas buscar, comparar y recuperar tus dictados</td></tr>
<tr><td>Portapapeles: antes de pegar un dictado, se guarda como texto lo que tenías copiado (no se guardan imágenes ni archivos)</td><td>Archivo en la carpeta de datos</td><td>Que no pierdas lo que habías copiado</td></tr>
<tr><td>Clave de IA y ajustes (atajos, capturas)</td><td>Archivos en la carpeta de datos</td><td>Que la app funcione con tu configuración</td></tr>
<tr><td>Capturas de pantalla (si activás esa función)</td><td>Portapapeles y, si lo dejás activado, la carpeta Imágenes\\WhisperPRO</td><td>La función de captura que elegiste</td></tr>
<tr><td>Registro técnico (log)</td><td>Archivo en la carpeta de datos</td><td>Diagnosticar errores. No incluye el contenido de lo que dictás salvo que actives el modo de depuración</td></tr></table>
<p>La app registra únicamente en tu equipo y nunca envía estos archivos a FESTUDIOS.</p>

<h2 id="salen">3. Qué sale de tu equipo</h2>
<p>Cuando grabás con el atajo, el audio se envía por internet al servicio de transcripción y corrección que conectaste. Por defecto es <b>Groq</b> (Groq, Inc., Estados Unidos), usando <b>tu propia clave</b>. Después, el texto transcripto también se envía a un modelo de lenguaje de ese mismo proveedor para aplicar tus correcciones habladas. Eso significa que tus datos pueden tratarse fuera de la Argentina; esa transferencia la hacés vos al conectar tu clave y se rige por la política de privacidad y los términos del proveedor (groq.com).</p>
<p>Si configurás otro proveedor en los ajustes avanzados (por ejemplo OpenAI o Google Gemini), los datos van a ese proveedor y rigen sus políticas. Si no hay clave configurada, la aplicación puede usar un modelo de transcripción local en tu equipo (en la versión para desarrolladores), sin enviar nada.</p>
<p><b>Si no dictás, no sale nada.</b> La aplicación solo abre una página web cuando vos tocás un enlace (por ejemplo, para crear tu clave en Groq o visitar festudios.pro).</p>
<h3>Versión web para el teléfono</h3>
<p>Guarda tu clave y tu historial en el almacenamiento del navegador de tu teléfono. Solo puede conectarse a api.groq.com. FESTUDIOS no recibe esos datos.</p>

<h3>Si dejás tu mail en nuestra web</h3>
<p>En la página de descarga podés dejar tu correo para recibir el link del instalador y novedades de WhisperPRO. Lo guardamos en el sistema de contacto de FESTUDIOS (sobre infraestructura de nuestro proveedor de bases de datos), junto con la fecha y la página desde donde lo dejaste, y lo usamos solo para enviarte lo que pediste y, si lo aceptaste, novedades del producto. Cuando descargás con ese link registramos la fecha, la versión y una huella de tu conexión que cambia cada día y no permite reconstruir tu IP, solo para contar descargas. Podés pedir que lo borremos o darte de baja en cualquier momento escribiendo a {MAIL}. Esto ocurre en el sitio web, no dentro de la aplicación: la aplicación sigue sin cuenta ni telemetría.</p>

<h2 id="finalidad">4. Para qué se usan y por cuánto tiempo</h2>
<p>Los datos locales se usan únicamente para que la aplicación funcione y para que consultes tu propia memoria de voz. Permanecen en tu equipo hasta que los borres vos o desinstales la aplicación. FESTUDIOS no conserva copia alguna. El proveedor de IA conserva o descarta el audio según sus propias políticas; consultalas antes de usar el servicio.</p>
<p>Los datos que nos enviás por correo se usan solo para responderte y se conservan mientras sea necesario para atender tu consulta.</p>

<h2 id="borrar">5. Cómo borrar tus datos</h2>
<ul><li><b>Historial y portapapeles:</b> en el panel de la app, Ajustes → Privacidad y datos → «Borrar historial».</li>
<li><b>Todo lo demás:</b> en el mismo lugar, «Abrir» muestra la carpeta de datos; borrá los archivos que quieras o la carpeta entera. Al desinstalar la app podés borrar también la carpeta de datos (en la versión instalada, %APPDATA%\\WhisperPRO).</li>
<li><b>Capturas:</b> borrá la carpeta Imágenes\\WhisperPRO.</li>
<li><b>Tu clave de Groq:</b> podés revocarla o eliminarla desde tu cuenta en console.groq.com.</li>
<li><b>Versión web:</b> Ajustes → «Borrar historial» y «Quitar» la clave, o borrá los datos del sitio en el navegador.</li></ul>

<h2 id="derechos">6. Tus derechos</h2>
<p>De acuerdo con la Ley 25.326 de Protección de Datos Personales, tenés derecho a acceder, rectificar, actualizar y suprimir tus datos personales. Como FESTUDIOS no almacena datos de tu uso, estos derechos los ejercés directamente sobre tus archivos locales (ver sección 5) y, respecto del proveedor de IA, ante ese proveedor. Para los datos que nos hayas enviado por correo, escribinos a <a href="mailto:{MAIL}">{MAIL}</a> y respondemos en un plazo máximo de diez días corridos.</p>
<p>La AGENCIA DE ACCESO A LA INFORMACIÓN PÚBLICA, en su carácter de Órgano de Control de la Ley N° 25.326, tiene la atribución de atender las denuncias y reclamos que interpongan quienes resulten afectados en sus derechos por incumplimiento de las normas vigentes en materia de protección de datos personales.</p>
<p>Si estás en el Espacio Económico Europeo o en el Reino Unido, también podés ejercer los derechos que te reconoce el RGPD (acceso, rectificación, supresión, limitación, portabilidad y oposición) escribiéndonos al mismo correo.</p>

<h2 id="seguridad">7. Seguridad</h2>
<p>Los archivos locales se guardan en tu carpeta de usuario <b>sin cifrar</b>, igual que cualquier documento tuyo: protegé tu equipo con las medidas habituales (contraseña de Windows, cifrado de disco). La aplicación no abre puertos ni acepta conexiones entrantes, y su interfaz está configurada para no poder conectarse a internet por sí sola. La clave de IA se guarda localmente en un archivo de configuración; no la compartas.</p>

<h2 id="sitio">8. Este sitio web y cookies</h2>
<p>Este sitio no usa cookies ni herramientas de análisis o publicidad de terceros, y carga sus tipografías desde el propio sitio. Como cualquier sitio web, el servidor puede registrar datos técnicos de la visita (dirección IP, fecha, página solicitada) con fines de seguridad y funcionamiento. Los enlaces a festudios.pro incluyen un parámetro (utm_source=whisperpro) que solo se usa si tocás el enlace, para saber desde dónde llegaste. Si en el futuro agregamos analítica o cookies, actualizaremos esta página y pediremos tu consentimiento donde corresponda.</p>

<h2 id="menores">9. Menores</h2>
<p>WhisperPRO no está dirigido a menores de 13 años y no recopilamos intencionalmente datos de menores. Si sos madre, padre o tutor y creés que un menor nos envió datos, escribinos y los eliminamos.</p>

<h2 id="cambios">10. Cambios y contacto</h2>
<p>Si esta política cambia de forma relevante, actualizaremos la fecha y, cuando corresponda, lo avisaremos dentro de la aplicación. Consultas sobre privacidad: <a href="mailto:{MAIL}">{MAIL}</a>. Más información: <a href="terminos/">Términos y condiciones</a> · <a href="contacto/">Contacto</a>.</p>
"""

TERM = f"""
<p>Estos términos regulan el uso de WhisperPRO, la aplicación de dictado por voz para Windows y su versión web («el Servicio»), ofrecida por {EMISOR} («FESTUDIOS», «nosotros»). Al instalar o usar el Servicio aceptás estos términos y la <a href="privacidad/">Política de privacidad</a>. Si no estás de acuerdo, no lo uses.</p>

<h2>1. Quién ofrece el Servicio</h2>
<p>{EMISOR} (marca «FESTUDIOS»), Argentina. Contacto: <a href="mailto:{MAIL}">{MAIL}</a>. Domicilio: Independencia 3800, Olavarría, Buenos Aires. CUIT: 20-36215734-0. Atención: lunes a viernes de 8 a 18 h.</p>

<h2>2. Qué es WhisperPRO</h2>
<p>Es una herramienta que convierte tu voz en texto y aplica correcciones habladas, guarda tu historial en tu equipo y ofrece accesorios como atajos y capturas de pantalla. Para transcribir usa el servicio de IA que conectás con tu propia clave (por defecto, Groq). Podemos agregar, cambiar o quitar funciones; lo haremos procurando no afectar lo esencial del plan gratuito.</p>

<h2>3. Licencia de uso</h2>
<p>Te otorgamos una licencia personal, no exclusiva, intransferible y revocable para instalar y usar el software en tus equipos, para uso personal o profesional propio. No podés: (a) copiar, vender, alquilar o redistribuir el software sin nuestro permiso por escrito; (b) quitar avisos de propiedad o marcas; (c) intentar eludir las limitaciones de un plan; (d) hacer ingeniería inversa, salvo en la medida en que la ley lo permita expresamente; (e) usarlo para fines ilícitos. Algunos componentes son de terceros y se rigen por sus propias licencias (ver <a href="licencias/">Licencias</a>).</p>

<h2>4. Tu clave y los servicios de terceros</h2>
<p>El Servicio funciona con servicios de terceros (como Groq) a los que accedés con tu propia clave. Vos sos responsable de: obtener la clave, cumplir los términos del proveedor, los límites de uso y los costos que el proveedor te cobre. FESTUDIOS no controla esos servicios, no responde por su disponibilidad, cambios, límites o políticas, y no tiene acceso a tu clave ni a tu cuenta.</p>

<h2>5. Uso aceptable y responsabilidad por lo que grabás</h2>
<ul><li>Sos el único responsable del contenido que dictás y de cómo lo usás.</li>
<li>No grabes a otras personas sin que lo sepan o sin el consentimiento que exija la ley donde estés. La grabación de conversaciones ajenas puede ser ilegal.</li>
<li>No lo uses para actividades ilícitas, para vulnerar derechos de terceros ni como único medio en situaciones críticas (emergencias, decisiones médicas, legales o financieras): las transcripciones pueden contener errores y tenés que revisarlas.</li></ul>

<h2>6. Tu contenido</h2>
<p>Lo que dictás y lo que se guarda en tu equipo es tuyo. FESTUDIOS no accede a ese contenido ni reclama derechos sobre él. Nos otorgás únicamente lo necesario para que la aplicación procese tu contenido en tu equipo y lo envíe al proveedor que elegiste.</p>

<h2>7. Planes</h2>
<h3>7.1 Plan gratuito</h3>
<p>Incluye las funciones esenciales descriptas en nuestra página, sin costo y sin límites impuestos por FESTUDIOS (los límites del proveedor de IA siguen aplicando).</p>
<h3>7.2 Plan Pro (desde su lanzamiento)</h3>
<p>El plan Pro agrega herramientas accesorias. Sus condiciones se aplican a partir de su lanzamiento y se informarán antes de contratar:</p>
<ul><li><b>Precio y moneda:</b> el plan Pro cuesta US$ 5 por mes. Como el pago es por transferencia en pesos argentinos, el monto en pesos se calcula con el dólar oficial (precio vendedor) del día del pago y se te informa antes de transferir, con los impuestos que correspondan.</li>
<li><b>Pago:</b> por transferencia bancaria. Pedís el plan en la página <a href="pro/">Contratar Pro</a>, confirmás tu correo y te mostramos y enviamos los datos de la cuenta; una vez acreditado el pago te enviamos tu licencia por correo. Emitimos el comprobante que corresponda.</li>
<li><b>Renovación:</b> mensual. Podés darte de baja en cualquier momento; la baja rige desde el fin del período ya pagado, sin permanencia mínima ni penalidades.</li>
<li><b>Cambios de precio:</b> los informamos con al menos 30 días de anticipación y no afectan períodos ya pagados.</li>
<li><b>Falta de pago:</b> si no se renueva el pago, el plan Pro deja de estar activo y la aplicación sigue funcionando con las funciones gratuitas. No se acumulan deudas ni intereses.</li>
<li><b>Cómo cancelar y arrepentirte:</b> ver <a href="baja-y-arrepentimiento/">Cancelar o arrepentirte</a>.</li></ul>

<h2>8. Derecho de arrepentimiento y defensa del consumidor</h2>
<p>Si contratás un servicio pago a distancia como consumidor, tenés derecho a revocar la contratación dentro de los diez (10) días corridos de celebrada, sin costo ni responsabilidad, conforme el artículo 34 de la Ley 24.240 y los artículos 1110 y siguientes del Código Civil y Comercial. Te devolvemos lo pagado por el mismo medio de pago. Cómo ejercerlo: <a href="baja-y-arrepentimiento/">Cancelar o arrepentirte</a>.</p>
<p>Defensa del Consumidor: podés presentar reclamos ante la Dirección Nacional de Defensa del Consumidor y Arbitraje del Consumo o ante la autoridad local de tu jurisdicción: <a href="{DEFENSA}" rel="noopener">argentina.gob.ar/produccion/defensadelconsumidor</a>.</p>

<h2>9. Propiedad intelectual</h2>
<p>El software, el nombre y el logo de WhisperPRO, la marca FESTUDIOS, el personaje «el Guía», los textos y las imágenes del Servicio son de FESTUDIOS o de sus licenciantes, y están protegidos por la ley. Estos términos no te transfieren ningún derecho sobre ellos más allá de la licencia del punto 3. El nombre «WhisperPRO» puede cambiar en el futuro; lo informaremos.</p>

<h2>10. Disponibilidad, garantías y límite de responsabilidad</h2>
<p>El Servicio se ofrece «tal cual está». No garantizamos que funcione sin interrupciones ni errores, ni que las transcripciones sean exactas. En la medida en que la ley lo permita y sin afectar los derechos que la Ley 24.240 reconoce a los consumidores, FESTUDIOS no responde por daños indirectos, lucro cesante o pérdida de datos, y, en el plan Pro, su responsabilidad total se limita a lo abonado en los últimos tres (3) períodos. Nada de lo aquí dispuesto excluye responsabilidad por dolo o culpa grave ni por lo que la ley no permita excluir.</p>

<h2>11. Suspensión y terminación</h2>
<p>Podés dejar de usar el Servicio y desinstalarlo cuando quieras. Podemos suspender o dar por terminado el acceso a funciones pagas si incumplís estos términos, con aviso previo salvo casos graves.</p>

<h2>12. Cambios en estos términos</h2>
<p>Podemos actualizar estos términos. Publicaremos la versión nueva con su fecha y, si el cambio es relevante, lo avisaremos en la aplicación o por correo con al menos 30 días de anticipación antes de que se aplique a planes pagos. Seguir usando el Servicio después implica aceptar la versión vigente.</p>

<h2>13. Ley aplicable y jurisdicción</h2>
<p>Estos términos se rigen por las leyes de la República Argentina. Para cualquier controversia serán competentes los tribunales ordinarios de la Ciudad Autónoma de Buenos Aires, sin perjuicio del derecho del consumidor de recurrir a los tribunales de su domicilio.</p>

<h2>14. Contacto</h2>
<p>Consultas, soporte o reclamos: <a href="mailto:{MAIL}">{MAIL}</a> (primera respuesta en 24 horas hábiles). Ver también <a href="contacto/">Contacto</a>.</p>
"""

BAJA = f"""
<p>Esta página explica cómo dar de baja una suscripción paga o ejercer el derecho de arrepentimiento. El plan <b>gratuito</b> no tiene pagos: lo desinstalás y listo. Las opciones de abajo aplican al <b>plan Pro</b>, que todavía no está disponible; la página queda lista para cuando se lance.</p>

<h2>Dar de baja tu suscripción</h2>
<ul><li>Podés cancelar en cualquier momento, sin permanencia mínima ni penalidades.</li>
<li>La baja rige desde el fin del período ya pagado: hasta entonces seguís usando Pro.</li>
<li>Después, la aplicación sigue funcionando con las funciones gratuitas.</li></ul>
<p><a class="btn" href="mailto:{MAIL}?subject=Baja%20de%20mi%20suscripci%C3%B3n%20WhisperPRO%20Pro&amp;body=Quiero%20dar%20de%20baja%20mi%20suscripci%C3%B3n.%0A%0ANombre%3A%0ACorreo%20con%20el%20que%20pagu%C3%A9%3A%0AMotivo%20(opcional)%3A">Pedir la baja</a></p>

<h2>Botón de arrepentimiento</h2>
<p>Si contrataste Pro como consumidor, podés arrepentirte dentro de los <b>diez (10) días corridos</b> de la contratación, sin costo ni necesidad de explicar el motivo. Te devolvemos lo que pagaste por el mismo medio de pago.</p>
<p><a class="btn s" href="mailto:{MAIL}?subject=Arrepentimiento%20de%20compra%20WhisperPRO%20Pro&amp;body=Quiero%20ejercer%20mi%20derecho%20de%20arrepentimiento.%0A%0ANombre%3A%0ACorreo%20con%20el%20que%20pagu%C3%A9%3A%0AFecha%20de%20contrataci%C3%B3n%3A">Ejercer el arrepentimiento</a></p>
<p>Respondemos dentro de las 24 horas hábiles y te confirmamos por escrito. Si tenés problemas con este medio, escribinos a <a href="mailto:{MAIL}">{MAIL}</a>.</p>

<h2>Más información</h2>
<p>Ver <a href="terminos/">Términos y condiciones</a> (puntos 7 y 8). Defensa del Consumidor: <a href="{DEFENSA}" rel="noopener">argentina.gob.ar/produccion/defensadelconsumidor</a>.</p>
"""

CONTACTO = f"""
<p>WhisperPRO es una herramienta de <b>FESTUDIOS</b>, un estudio argentino que diseña y desarrolla webs, sistemas y apps a medida para negocios. Conocé el resto de nuestro trabajo en <a href="https://festudios.pro/?utm_source=whisperpro&amp;utm_medium=contacto&amp;utm_campaign=quienes-somos">festudios.pro</a>.</p>

<h2>Escribinos</h2>
<table><tr><th>Para</th><th>Cómo</th></tr>
<tr><td>Soporte, errores y consultas sobre WhisperPRO</td><td><a href="mailto:{MAIL}?subject=Soporte%20WhisperPRO">{MAIL}</a></td></tr>
<tr><td>Privacidad y datos personales</td><td><a href="mailto:{MAIL}?subject=Privacidad%20WhisperPRO">{MAIL}</a></td></tr>
<tr><td>Baja, arrepentimiento y facturación (plan Pro)</td><td><a href="baja-y-arrepentimiento/">Cancelar o arrepentirte</a></td></tr>
<tr><td>Un proyecto a medida para tu negocio</td><td><a href="https://festudios.pro/?utm_source=whisperpro&amp;utm_medium=contacto&amp;utm_campaign=proyecto">festudios.pro</a></td></tr></table>
<p><b>Horario de atención:</b> lunes a viernes, de 8 a 18 h (Argentina). <b>Primera respuesta:</b> dentro de las 24 horas hábiles.</p>

<h2>Datos del proveedor</h2>
<table><tr><th>Dato</th><th>Detalle</th></tr>
<tr><td>Nombre</td><td>{EMISOR} (marca «FESTUDIOS»)</td></tr>
<tr><td>CUIT</td><td>20-36215734-0</td></tr>
<tr><td>Domicilio comercial</td><td>Independencia 3800, Olavarría, Buenos Aires, Argentina</td></tr>
<tr><td>Correo</td><td><a href="mailto:{MAIL}">{MAIL}</a></td></tr></table>
<p>Defensa del Consumidor: <a href="{DEFENSA}" rel="noopener">argentina.gob.ar/produccion/defensadelconsumidor</a>.</p>

<h2>Más información</h2>
<p><a href="privacidad/">Política de privacidad</a> · <a href="terminos/">Términos y condiciones</a> · <a href="licencias/">Licencias de terceros</a>.</p>
"""

LIC = f"""
<p>WhisperPRO está hecho por FESTUDIOS y usa componentes de terceros que se distribuyen con sus propias licencias. Agradecemos a sus autores. Esta lista resume los principales; los textos completos de cada licencia están disponibles en los proyectos originales y, para las tipografías, en la carpeta <code>fonts</code> de este sitio.</p>

<h2>Tipografías</h2>
<table><tr><th>Componente</th><th>Licencia</th></tr>
<tr><td>Bricolage Grotesque — © 2022 The Bricolage Grotesque Project Authors</td><td>SIL Open Font License 1.1</td></tr>
<tr><td>Martian Mono — © Evil Martians y colaboradores</td><td>SIL Open Font License 1.1</td></tr></table>
<p>Las licencias de las dos tipografías están en <a href="fonts/LICENCIA-Bricolage-Grotesque-OFL.txt">LICENCIA-Bricolage-Grotesque-OFL.txt</a> y <a href="fonts/LICENCIA-Martian-Mono-OFL.txt">LICENCIA-Martian-Mono-OFL.txt</a>.</p>

<h2>Aplicación de escritorio</h2>
<table><tr><th>Componente</th><th>Licencia</th></tr>
<tr><td>Python</td><td>Python Software Foundation License</td></tr>
<tr><td>NumPy</td><td>BSD-3-Clause</td></tr>
<tr><td>sounddevice</td><td>MIT</td></tr>
<tr><td>keyboard</td><td>MIT</td></tr>
<tr><td>pyperclip</td><td>BSD-3-Clause</td></tr>
<tr><td>python-dotenv</td><td>BSD-3-Clause</td></tr>
<tr><td>Pillow</td><td>MIT-CMU (HPND)</td></tr>
<tr><td>pywebview</td><td>BSD-3-Clause</td></tr>
<tr><td>pystray</td><td>LGPL-3.0</td></tr>
<tr><td>Groq SDK, OpenAI SDK, Google Gen AI SDK</td><td>Apache-2.0</td></tr>
<tr><td>faster-whisper (modo local, versión para desarrolladores)</td><td>MIT</td></tr>
<tr><td>PyInstaller (empaquetado)</td><td>GPL-2.0 con excepción para aplicaciones empaquetadas</td></tr>
<tr><td>Inno Setup (instalador)</td><td>Inno Setup License</td></tr>
<tr><td>Microsoft Edge WebView2 Runtime</td><td>Términos de Microsoft</td></tr></table>

<h2>Servicios de terceros</h2>
<p>La transcripción y la corrección se hacen con servicios externos que conectás con tu propia clave (por defecto, Groq). Su uso se rige por los términos y la política de privacidad de cada proveedor. Los nombres y marcas de terceros mencionados pertenecen a sus dueños y se usan solo para identificar compatibilidad.</p>

<h2>Marcas</h2>
<p>«FESTUDIOS», «WhisperPRO» y el personaje «el Guía» son de FESTUDIOS. WhisperPRO es independiente y no está afiliado a OpenAI, Groq ni Microsoft. Más en <a href="terminos/">Términos y condiciones</a>.</p>
"""


def _fig(archivo, alt, pie):
    """Captura opcional: si el archivo existe en landing/img, se muestra; si no, no se muestra nada."""
    if not os.path.exists(os.path.join(RAIZ, "img", archivo)):
        return ""
    return f'<figure><img src="img/{archivo}" alt="{alt}" width="1000" loading="lazy"><figcaption>{pie}</figcaption></figure>'


CLAVE = f"""
<h2 id="clave">Cómo conseguir tu clave gratis de IA (1 minuto)</h2>
<p>WhisperPRO usa Groq para transcribir tu voz. Necesitás una <b>clave gratuita</b> (una especie de contraseña propia). Se consigue una sola vez, en tres toques. <b>No hace falta tarjeta.</b></p>

<div class="paso"><span class="n">1</span><div><h3>Entrá a Groq con tu cuenta de Google</h3>
<p>Abrí <a href="https://console.groq.com/keys" target="_blank" rel="noopener">console.groq.com/keys</a> y elegí <span class="kbd">Continue with Google</span> (también podés entrar con GitHub o con tu mail). La cuenta es gratis.</p>
{_fig("groq-1.png", "Pantalla de inicio de sesión de Groq", "Captura real de Groq: elegí «Continue with Google» o el método que prefieras.")}</div></div>

<div class="paso"><span class="n">2</span><div><h3>Creá la clave</h3>
<p>Una vez dentro, en la sección <b>API Keys</b>, tocá <span class="kbd">Create API Key</span>.</p>
{_fig("groq-2.png", "Sección API Keys de Groq con el botón Create API Key", "Ilustración. (1) Tocá «Create API Key». La pantalla de Groq puede variar un poco.")}
<p>Se abre una ventana: en <span class="kbd">Display Name</span> escribí cualquier nombre (por ejemplo «WhisperPRO»), dejá <span class="kbd">Expiration</span> en <span class="kbd">No expiration</span> para que la clave no venza, y esperá un segundo a que <b>Cloudflare</b> termine de verificar que sos una persona (se tilda solo). Después confirmá con el botón de crear de esa ventana.</p>
{_fig("groq-3.png", "Ventana Create API Key de Groq con el nombre y la verificación de Cloudflare", "Ilustración. (1) Poné un nombre, (2) dejá «No expiration» y (3) esperá la verificación de Cloudflare.")}</div></div>

<div class="paso"><span class="n">3</span><div><h3>Copiala</h3>
<p>Groq te muestra la clave nueva. Apretá <span class="kbd">Copy</span>. Empieza con <span class="kbd">gsk_</span> y la muestra <b>una sola vez</b>. No hace falta que la guardes ni la pegues en ningún lado: WhisperPRO la toma del portapapeles.</p>
{_fig("groq-4.png", "Clave nueva en Groq con el botón Copy", "Apretá Copy.")}</div></div>

<h2 id="poner">Cómo ponerla en WhisperPRO</h2>
<p>Abrí WhisperPRO por primera vez: aparece solo la pantalla <b>«Conectá WhisperPRO»</b>, con el Guía.</p>
<figure><img src="img/conexion-1.webp" alt="Pantalla Conectá WhisperPRO con tres pasos y el Guía" width="1000" loading="lazy"><figcaption>La pantalla de conexión se abre sola la primera vez.</figcaption></figure>
<ol>
<li>Tocá <span class="kbd">Abrir Groq</span>: se abre la página de las claves en tu navegador.</li>
<li>Hacé los pasos de arriba y apretá <span class="kbd">Copy</span>. Después volvé a WhisperPRO.</li>
<li><b>WhisperPRO detecta la clave sola</b>, la prueba y la guarda. Cuando termina dice «Listo, conectado».</li>
</ol>
<figure><img src="img/conexion-3.webp" alt="Pantalla de WhisperPRO que dice Listo, conectado" width="1000" loading="lazy"><figcaption>Cuando dice «Listo, conectado», ya podés dictar con <span class="kbd">Win + Espacio</span>.</figcaption></figure>

<div class="box">
<p style="margin:0 0 8px"><b>¿No la detectó?</b></p>
<p style="margin:0">Pegá la clave en el cuadro «¿No la detectó? Pegala acá: gsk_…» y tocá <span class="kbd">Conectar</span>. Más adelante podés cambiarla desde el ícono de WhisperPRO junto al reloj → <span class="kbd">Cambiar clave de IA</span>.</p>
</div>

<h3>Cosas que conviene saber</h3>
<ul>
<li>Tu clave queda <b>solo en tu PC</b>. FESTUDIOS no la ve ni la guarda.</li>
<li>No la compartas con nadie: es como una contraseña. Si la perdés o la mostraste sin querer, creá otra en Groq y cambiala en WhisperPRO.</li>
<li>El plan gratuito de Groq tiene límites de uso. Para dictar normalmente alcanza de sobra.</li>
<li>Si «Abrir Groq» no abre nada, entrá a mano a <b>console.groq.com/keys</b>.</li>
</ul>
"""

DESCARGAR = f"""
<p>WhisperPRO es gratis para empezar: dictás en cualquier programa de Windows con un atajo, sin cuenta.</p>
<div class="box" id="caja">
<form id="f" novalidate>
<p style="margin:0 0 10px"><b id="t">Dejá tu mail y te enviamos el link de descarga.</b></p>
<p style="margin:0 0 14px"><input id="m" type="email" required autocomplete="email" placeholder="tu@mail.com" style="width:100%;max-width:420px;padding:13px 14px;border-radius:12px;border:1px solid #2a2e3d;background:#0a0b10;color:#fff;font:inherit"></p>
<p style="margin:0 0 14px;font-size:15px"><label><input id="c" type="checkbox" required> Acepto que FESTUDIOS me escriba a este mail con el link y novedades de WhisperPRO. Puedo darme de baja cuando quiera. <a href="privacidad/">Privacidad</a></label></p>
<button class="btn" type="submit" style="border:0;cursor:pointer;font-family:inherit">Enviarme el link</button>
<p id="e" style="color:#fda4af;margin:12px 0 0" role="alert"></p>
</form>
<div id="ok" style="display:none" role="status" aria-live="polite"><div class="exito"><div class="tilde" aria-hidden="true">✓</div><h2>¡Listo! Te enviamos un mail</h2><div class="mail" id="okmail"></div><p style="margin:0">Tocá el link que te mandamos para bajar el instalador (vale 48 horas).</p><ol><li>Abrí tu correo.</li><li>Buscá «Tu descarga de WhisperPRO».</li><li>Tocá el link y se baja el instalador para Windows 10 y 11 (64 bits).</li></ol><p class="chico">El mail llega de «WhisperPRO por FESTUDIOS». Si en unos minutos no aparece, revisá la carpeta de correo no deseado o <a href="#" id="otro">probá con otro mail</a>.</p><p class="chico">Mientras esperás: <a href="descargar/#clave">cómo conseguir tu clave gratis de IA</a>, que vas a necesitar al abrir WhisperPRO.</p></div></div>
<div id="warn" style="display:none" role="alert"><div class="aviso"><h2>Recibimos tu pedido, pero no pudimos enviar el mail</h2><p style="margin:0">Hubo un problema de nuestro lado al mandarlo. No hace falta que repitas nada: ya quedó anotado y te lo enviamos a mano. Si querés apurarlo, escribinos a {MAIL}.</p></div></div>
</div>
<p class="mono" style="font-size:13px">Si Windows muestra «Windows protegió su PC», tocá «Más información» y después «Ejecutar de todas formas». Es normal en aplicaciones nuevas.</p>
<div class="box" id="movil"><p style="margin:0 0 8px"><b>¿Desde el teléfono?</b></p><p style="margin:0 0 14px">El instalador es para Windows. En iPhone y Android usá la versión web: se abre en el navegador y la podés agregar a tu pantalla de inicio como una app.</p><a class="btn" href="app/">Abrir la versión web</a></div>
{CLAVE}
<script>if(/Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)){{var m=document.getElementById('movil'),c=document.getElementById('caja');c.parentNode.insertBefore(m,c);document.getElementById('t').textContent='Para bajarlo en tu PC, dejá tu mail y te enviamos el link.';}}
document.getElementById('f').addEventListener('submit',async function(ev){{
  ev.preventDefault();var e=document.getElementById('e'),m=document.getElementById('m').value.trim();
  e.textContent='';
  if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(m)){{e.textContent='Ese mail no parece válido. Escribilo así: tu@mail.com';return;}}
  if(!document.getElementById('c').checked){{e.textContent='Marcá la casilla para continuar.';return;}}
  var bt=document.querySelector('#f button'),bt0=bt.innerHTML;bt.disabled=true;bt.innerHTML='<span class="spin"></span>Enviando…';
  try{{
    var r=await fetch('api/solicitar.php',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:m,consentimiento:true,origen:'whisperpro-descarga',dispositivo:/Mobi|Android/i.test(navigator.userAgent)?'celular':'compu'}})}});
    if(r.status===429){{e.textContent='Demasiados pedidos seguidos. Probá en un rato.';bt.disabled=false;bt.innerHTML=bt0;return;}}
    if(!r.ok)throw 0;
    var j={{}};try{{j=await r.json();}}catch(z){{}}document.getElementById('f').style.display='none';document.getElementById('okmail').textContent=m;document.getElementById(j.enviado===false?'warn':'ok').style.display='block';window.scrollTo({{top:document.getElementById('caja').offsetTop-20,behavior:'smooth'}});
  }}catch(x){{bt.disabled=false;bt.innerHTML=bt0;e.textContent='No pudimos enviar el link. Probá de nuevo o escribinos a {MAIL}.';}}
}});
document.getElementById('otro').addEventListener('click',function(ev){{ev.preventDefault();document.getElementById('ok').style.display='none';document.getElementById('f').style.display='';document.getElementById('m').focus();}});
</script>
"""

PRO_PAGE = f"""
<p>WhisperPRO Pro suma atajos a tu medida, un segundo atajo y las capturas de pantalla. Cuesta <b>US$ 5 por mes</b> <span id="ars" class="mono"></span>. Antes de pagar podés <b>probarlo 1 mes gratis</b> desde Ajustes, sin tarjeta ni datos.</p>
<ol>
<li>Dejás tu mail y lo confirmás con el link que te enviamos.</li>
<li>Te mostramos y te enviamos por mail los datos para transferir (con el monto en pesos de hoy).</li>
<li>Transferís y respondés el mail con el comprobante.</li>
<li>Te enviamos tu licencia y la activás en WhisperPRO → Ajustes → Activar Pro.</li>
</ol>
<div class="box" id="caja">
<form id="f" novalidate>
<p style="margin:0 0 14px"><input id="m" type="email" required autocomplete="email" placeholder="tu@mail.com" style="width:100%;max-width:420px;padding:13px 14px;border-radius:12px;border:1px solid #2a2e3d;background:#0a0b10;color:#fff;font:inherit"></p>
<p style="margin:0 0 14px;font-size:15px"><label><input id="c" type="checkbox" required> Acepto que FESTUDIOS me escriba a este mail por mi pedido y con novedades de WhisperPRO. Puedo darme de baja cuando quiera. <a href="privacidad/">Privacidad</a> · <a href="terminos/">Términos</a></label></p>
<button class="btn" type="submit" style="border:0;cursor:pointer;font-family:inherit">Quiero el plan Pro</button>
<p id="e" style="color:#fda4af;margin:12px 0 0" role="alert"></p>
</form>
<div id="ok" style="display:none" role="status" aria-live="polite"><div class="exito"><div class="tilde" aria-hidden="true">✓</div><h2>¡Listo! Te enviamos un mail</h2><div class="mail" id="okmail"></div><p style="margin:0">Confirmá que es tuyo para ver los datos de pago (el link vale 48 horas).</p><ol><li>Abrí tu correo.</li><li>Buscá «Confirmá tu mail para contratar WhisperPRO Pro».</li><li>Tocá el link: te mostramos y te enviamos los datos para transferir.</li></ol><p class="chico">El mail llega de «WhisperPRO por FESTUDIOS». Si en unos minutos no aparece, revisá la carpeta de correo no deseado o <a href="#" id="otro">probá con otro mail</a>.</p><p class="chico">Mientras esperás: <a href="descargar/#clave">cómo conseguir tu clave gratis de IA</a>, que vas a necesitar al abrir WhisperPRO.</p></div></div>
<div id="warn" style="display:none" role="alert"><div class="aviso"><h2>Recibimos tu pedido, pero no pudimos enviar el mail</h2><p style="margin:0">Hubo un problema de nuestro lado al mandarlo. No hace falta que repitas nada: ya quedó anotado y te lo enviamos a mano. Si querés apurarlo, escribinos a {MAIL}.</p></div></div>
</div>
<p class="mono" style="font-size:13px">Pagás por transferencia bancaria. Tenés 10 días corridos para arrepentirte y podés darte de baja cuando quieras: <a href="baja-y-arrepentimiento/">cómo hacerlo</a>.</p>
<script>
fetch('api/dolar.php').then(function(r){{return r.ok?r.json():Promise.reject();}}).then(function(d){{
  if(d&&d.venta)document.getElementById('ars').textContent='(≈ $'+(Math.round(5*d.venta/50)*50).toLocaleString('es-AR')+' ARS al dólar oficial de hoy)';
}}).catch(function(){{}});
document.getElementById('f').addEventListener('submit',async function(ev){{
  ev.preventDefault();var e=document.getElementById('e'),m=document.getElementById('m').value.trim();
  e.textContent='';
  if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(m)){{e.textContent='Ese mail no parece válido. Escribilo así: tu@mail.com';return;}}
  if(!document.getElementById('c').checked){{e.textContent='Marcá la casilla para continuar.';return;}}
  var bt=document.querySelector('#f button'),bt0=bt.innerHTML;bt.disabled=true;bt.innerHTML='<span class="spin"></span>Enviando…';
  try{{
    var r=await fetch('api/contratar.php',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:m,consentimiento:true}})}});
    if(r.status===429){{e.textContent='Demasiados pedidos seguidos. Probá en un rato.';bt.disabled=false;bt.innerHTML=bt0;return;}}
    if(!r.ok)throw 0;
    var j={{}};try{{j=await r.json();}}catch(z){{}}document.getElementById('f').style.display='none';document.getElementById('okmail').textContent=m;document.getElementById(j.enviado===false?'warn':'ok').style.display='block';window.scrollTo({{top:document.getElementById('caja').offsetTop-20,behavior:'smooth'}});
  }}catch(x){{bt.disabled=false;bt.innerHTML=bt0;e.textContent='No pudimos enviar el mail. Probá de nuevo o escribinos a {MAIL}.';}}
}});
document.getElementById('otro').addEventListener('click',function(ev){{ev.preventDefault();document.getElementById('ok').style.display='none';document.getElementById('f').style.display='';document.getElementById('m').focus();}});
</script>
"""

CUERPOS = {
    "privacidad": ("Política de privacidad", "Qué datos guarda WhisperPRO, dónde, y lo único que sale de tu equipo cuando dictás. Sin cuenta, sin telemetría.", PRIV),
    "terminos": ("Términos y condiciones", "Condiciones de uso de WhisperPRO: licencia, planes, derecho de arrepentimiento, responsabilidad y ley aplicable.", TERM),
    "baja-y-arrepentimiento": ("Cancelar o arrepentirte", "Cómo dar de baja una suscripción de WhisperPRO Pro y cómo ejercer el derecho de arrepentimiento en 10 días.", BAJA),
    "contacto": ("Contacto y datos del proveedor", "Cómo contactar a FESTUDIOS, horarios de atención y datos del proveedor de WhisperPRO.", CONTACTO),
    "descargar": ("Descargar WhisperPRO", "Descargá WhisperPRO para Windows: dictado por voz en cualquier programa, gratis para empezar.", DESCARGAR),
    "pro": ("Contratar WhisperPRO Pro", "Contratá el plan Pro de WhisperPRO: US$ 5 por mes, atajos a tu medida y capturas de pantalla. Probalo 1 mes gratis.", PRO_PAGE),
    "licencias": ("Licencias de terceros", "Componentes de terceros que usa WhisperPRO y sus licencias.", LIC),
}

if __name__ == "__main__":
    for ruta, (titulo, desc, cuerpo) in CUERPOS.items():
        os.makedirs(os.path.join(RAIZ, ruta), exist_ok=True)
        with open(os.path.join(RAIZ, ruta, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina(ruta, titulo, desc, cuerpo))
    urls = [("", "1.0"), ("descargar/", "0.8"), ("pro/", "0.7"), ("app/", "0.6")] + [(r + "/", "0.5") for r, _ in PAGINAS]
    items = "\n".join(f"  <url><loc>{BASE}{u}</loc><lastmod>{FECHA_ISO}</lastmod><priority>{p}</priority></url>" for u, p in urls)
    with open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n')
    print("páginas legales y sitemap.xml generados")
