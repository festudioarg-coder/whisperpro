<?php
/**
 * _plantilla.php — mails institucionales de WhisperPRO / FESTUDIOS.
 * HTML de tablas con estilos en línea (lo único que respetan todos los clientes de correo), sin tipografías ni
 * imágenes de terceros: solo el logo propio, con texto alternativo. Siempre se manda junto a una versión de texto.
 */
declare(strict_types=1);

const WP_SITIO   = 'https://festudios.pro/whisperpro/';
const WP_LOGO    = 'https://festudios.pro/whisperpro/img/logo-128.png';
const WP_EMISOR  = 'FESTUDIO ARGENTINA';
const WP_DATOS   = 'CUIT 20-36215734-0 · Independencia 3800, Olavarría, Buenos Aires, Argentina';

function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }

/** Botón principal (a prueba de Outlook: tabla con fondo + enlace). */
function mail_boton(string $texto, string $url): string {
    return '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:28px auto 6px"><tr>'
        . '<td align="center" bgcolor="#7c3aed" style="border-radius:12px;background:linear-gradient(160deg,#9b6bff 0%,#7c3aed 50%,#5b21b6 100%)">'
        . '<a href="' . h($url) . '" target="_blank" style="display:inline-block;padding:16px 34px;font:700 17px/1.2 Segoe UI,Helvetica,Arial,sans-serif;color:#ffffff;text-decoration:none;border-radius:12px">' . h($texto) . '</a>'
        . '</td></tr></table>';
}

/** Lista numerada de pasos. $pasos = ['texto', ...]. */
function mail_pasos(array $pasos): string {
    $f = '';
    foreach ($pasos as $i => $p) {
        $f .= '<tr><td width="34" valign="top" style="padding:7px 0"><table role="presentation" cellpadding="0" cellspacing="0"><tr><td align="center" width="26" height="26" bgcolor="#ede9fe" style="border-radius:13px;font:700 13px/26px Segoe UI,Arial,sans-serif;color:#5b21b6">' . ($i + 1) . '</td></tr></table></td>'
            . '<td valign="top" style="padding:7px 0;font:400 15.5px/1.55 Segoe UI,Helvetica,Arial,sans-serif;color:#374151">' . $p . '</td></tr>';
    }
    return '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:6px 0 0">' . $f . '</table>';
}

/** Tarjeta de datos (clave / valor), por ejemplo los datos de transferencia. */
function mail_datos(array $filas): string {
    $f = '';
    foreach ($filas as [$k, $v, $mono]) {
        $f .= '<tr><td style="padding:9px 16px;border-bottom:1px solid #e5e7eb;font:600 12px/1.4 Segoe UI,Arial,sans-serif;letter-spacing:.06em;color:#6b7280;text-transform:uppercase" width="38%">' . h($k) . '</td>'
            . '<td style="padding:9px 16px;border-bottom:1px solid #e5e7eb;font:' . ($mono ? '600 15px/1.4 Consolas,Menlo,monospace' : '600 15.5px/1.4 Segoe UI,Arial,sans-serif') . ';color:#111827' . ($mono ? ';word-break:break-all' : '') . '">' . h($v) . '</td></tr>';
    }
    return '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:18px 0;border:1px solid #e5e7eb;border-radius:12px;background:#f9fafb">' . $f . '</table>';
}

function mail_p(string $html, string $estilo = ''): string {
    return '<p style="margin:0 0 14px;font:400 16px/1.6 Segoe UI,Helvetica,Arial,sans-serif;color:#374151;' . $estilo . '">' . $html . '</p>';
}

/**
 * Mail completo.
 * $titulo: título grande · $preheader: la línea que se ve en la bandeja · $cuerpo: HTML ya armado
 * $porque: por qué recibe este mail (va en el pie)
 */
function mail_html(string $titulo, string $preheader, string $cuerpo, string $porque): string {
    $pie = '';
    foreach ([['Privacidad', 'privacidad/'], ['Términos', 'terminos/'], ['Contacto', 'contacto/']] as [$t, $r]) {
        $pie .= '<a href="' . WP_SITIO . $r . '" target="_blank" style="color:#6d28d9;text-decoration:none">' . $t . '</a> &nbsp;·&nbsp; ';
    }
    $pie .= '<a href="https://festudios.pro/" target="_blank" style="color:#6d28d9;text-decoration:none">festudios.pro</a>';

    return '<!doctype html><html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        . '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>' . h($titulo) . '</title></head>'
        . '<body style="margin:0;padding:0;background:#eceaf3;-webkit-text-size-adjust:100%">'
        . '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent">' . h($preheader) . str_repeat('&nbsp;&zwnj;', 40) . '</div>'
        . '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="#eceaf3"><tr><td align="center" style="padding:28px 12px">'
        . '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="width:100%;max-width:600px">'

        /* cabecera institucional */
        . '<tr><td bgcolor="#12081f" style="background:#12081f;background-image:linear-gradient(135deg,#1e0b3a 0%,#12081f 55%,#2a0f55 100%);border-radius:18px 18px 0 0;padding:30px 36px 26px">'
        . '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"><tr>'
        . '<td valign="middle" width="64"><img src="' . WP_LOGO . '" width="52" height="52" alt="WhisperPRO" style="display:block;border:0;border-radius:14px"></td>'
        . '<td valign="middle" style="padding-left:14px"><div style="font:700 11px/1.4 Segoe UI,Arial,sans-serif;letter-spacing:.2em;color:#c4b5fd">DESARROLLADO POR FESTUDIOS</div>'
        . '<div style="font:800 26px/1.15 Segoe UI,Helvetica,Arial,sans-serif;letter-spacing:-.02em;color:#ffffff">Whisper<span style="color:#c084fc">PRO</span></div></td>'
        . '</tr></table></td></tr>'

        /* franja de color */
        . '<tr><td height="4" style="height:4px;line-height:4px;font-size:0;background:#7c3aed;background-image:linear-gradient(90deg,#7c3aed,#c084fc,#f0abfc)">&nbsp;</td></tr>'

        /* cuerpo */
        . '<tr><td bgcolor="#ffffff" style="background:#ffffff;padding:38px 36px 30px">'
        . '<h1 style="margin:0 0 16px;font:800 28px/1.2 Segoe UI,Helvetica,Arial,sans-serif;letter-spacing:-.02em;color:#111827">' . h($titulo) . '</h1>'
        . $cuerpo
        . '</td></tr>'

        /* firma institucional */
        . '<tr><td bgcolor="#ffffff" style="background:#ffffff;padding:0 36px 34px"><table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-top:1px solid #e5e7eb"><tr><td style="padding-top:22px">'
        . '<div style="font:700 15px/1.4 Segoe UI,Arial,sans-serif;color:#111827">El equipo de FESTUDIOS</div>'
        . '<div style="font:400 14px/1.5 Segoe UI,Arial,sans-serif;color:#6b7280">Estudio argentino de desarrollo de software: webs, sistemas y apps a medida para negocios.</div>'
        . '<div style="font:400 14px/1.5 Segoe UI,Arial,sans-serif;color:#6b7280">¿Dudas? Respondé este mail y te contestamos una persona.</div>'
        . '</td></tr></table></td></tr>'

        /* pie legal */
        . '<tr><td bgcolor="#f6f5fa" style="background:#f6f5fa;border-radius:0 0 18px 18px;padding:22px 36px 26px;border-top:1px solid #e5e7eb">'
        . '<div style="font:400 13px/1.7 Segoe UI,Arial,sans-serif;color:#6b7280;text-align:center">' . $pie . '</div>'
        . '<div style="font:400 12px/1.6 Segoe UI,Arial,sans-serif;color:#9ca3af;text-align:center;margin-top:10px">' . h($porque) . ' Para borrar tus datos o no recibir más novedades, respondé con la palabra BAJA.</div>'
        . '<div style="font:400 12px/1.6 Segoe UI,Arial,sans-serif;color:#9ca3af;text-align:center;margin-top:10px">' . h(WP_EMISOR) . ' · ' . h(WP_DATOS) . '<br>Hecho en Argentina</div>'
        . '</td></tr>'
        . '</table></td></tr></table></body></html>';
}

/* ---------- Los tres mails ---------- */

function mail_descarga(string $link): array {
    $cuerpo = mail_p('Gracias por elegir WhisperPRO, la aplicación de dictado por voz para Windows que desarrollamos en FESTUDIOS. Tu descarga está lista.')
        . mail_boton('Descargar WhisperPRO para Windows', $link)
        . mail_p('El link vale 48 horas · Windows 10 y 11 (64 bits)', 'text-align:center;font-size:13.5px;color:#6b7280;margin-bottom:22px')
        . '<div style="font:700 13px/1.4 Segoe UI,Arial,sans-serif;letter-spacing:.1em;color:#6d28d9;margin:22px 0 4px">CÓMO EMPEZAR</div>'
        . mail_pasos([
            '<b>Instalá</b> el programa: abrí el archivo descargado y seguí el asistente.',
            '<b>Conectá tu clave gratuita de IA.</b> Al abrirlo te guiamos paso a paso; lleva un minuto.',
            '<b>Hablá.</b> Apretá <b>Win + Espacio</b> en cualquier programa y mirá cómo se escribe lo que decís.',
        ])
        . '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:24px 0 0"><tr><td bgcolor="#f5f3ff" style="background:#f5f3ff;border-radius:12px;padding:15px 18px;font:400 14.5px/1.55 Segoe UI,Arial,sans-serif;color:#4c1d95">'
        . '<b>Si Windows muestra «Windows protegió su PC»:</b> tocá «Más información» y después «Ejecutar de todas formas». Es normal en aplicaciones nuevas.</td></tr></table>'
        . mail_p('Si el botón no funciona, copiá este enlace en tu navegador:<br><a href="' . h($link) . '" style="color:#6d28d9;word-break:break-all;font-size:13px">' . h($link) . '</a>', 'margin-top:22px;font-size:13.5px;color:#6b7280');
    $texto = "Hola,\n\nGracias por elegir WhisperPRO, la aplicación de dictado por voz para Windows que desarrollamos en FESTUDIOS.\n\n"
        . "Tu link de descarga (vale 48 horas):\n$link\n\nPara Windows 10 y 11 (64 bits).\n\n"
        . "Cómo empezar:\n1) Instalá el programa.\n2) Conectá tu clave gratuita de IA: al abrirlo te guiamos, lleva un minuto.\n3) Apretá Win + Espacio en cualquier programa y hablá.\n\n"
        . "Si Windows muestra «Windows protegió su PC», tocá «Más información» y después «Ejecutar de todas formas»: es normal en aplicaciones nuevas.\n\n"
        . "¿Dudas? Respondé este mail.\n\nEl equipo de FESTUDIOS · festudios.pro\n" . WP_EMISOR . ' · ' . WP_DATOS . "\n\n"
        . "Recibís este mail porque pediste la descarga en festudios.pro/whisperpro. Para borrar tus datos o no recibir más novedades, respondé con la palabra BAJA.";
    return ['asunto' => 'Tu descarga de WhisperPRO está lista',
            'html' => mail_html('Tu descarga está lista', 'Tu link de descarga de WhisperPRO vale 48 horas.', $cuerpo, 'Recibís este mail porque pediste la descarga de WhisperPRO en festudios.pro.'),
            'texto' => $texto];
}

function mail_verificacion_pro(string $link): array {
    $cuerpo = mail_p('Pediste contratar <b>WhisperPRO Pro</b> (US$ 5 por mes). Antes de seguir, necesitamos confirmar que este mail es tuyo.')
        . mail_boton('Confirmar mi mail', $link)
        . mail_p('El link vale 48 horas', 'text-align:center;font-size:13.5px;color:#6b7280;margin-bottom:22px')
        . mail_p('Al confirmarlo te mostramos los datos para pagar por transferencia bancaria y te los enviamos también por mail. Antes de pagar, podés probar Pro <b>1 mes gratis</b> desde Ajustes, sin tarjeta.')
        . mail_p('Si no pediste esto, ignorá este mensaje: no pasa nada.', 'font-size:14px;color:#6b7280')
        . mail_p('Si el botón no funciona, copiá este enlace en tu navegador:<br><a href="' . h($link) . '" style="color:#6d28d9;word-break:break-all;font-size:13px">' . h($link) . '</a>', 'margin-top:18px;font-size:13.5px;color:#6b7280');
    $texto = "Hola,\n\nPediste contratar WhisperPRO Pro (US$ 5 por mes). Para confirmar que este mail es tuyo, tocá el link (vale 48 horas):\n\n$link\n\n"
        . "Al confirmarlo te mostramos los datos para pagar por transferencia bancaria y te los enviamos también por mail.\n\nSi no pediste esto, ignorá este mensaje.\n\nEl equipo de FESTUDIOS · festudios.pro\n" . WP_EMISOR . ' · ' . WP_DATOS;
    return ['asunto' => 'Confirmá tu mail para contratar WhisperPRO Pro',
            'html' => mail_html('Confirmá tu mail', 'Un paso más para contratar WhisperPRO Pro.', $cuerpo, 'Recibís este mail porque alguien pidió contratar WhisperPRO Pro con esta dirección.'),
            'texto' => $texto];
}

/** $filas = lista de [rótulo, valor, esMonoespaciado]. */
function mail_datos_pago(string $monto, string $ref, array $filas, bool $hayDatos): array {
    $tabla = mail_datos(array_merge([['Monto', $monto, false]], $filas, [['Referencia', $ref, true]]));
    $cuerpo = mail_p('Gracias por confirmar tu mail. Para activar <b>WhisperPRO Pro</b> (1 mes), hacé una transferencia con estos datos:')
        . $tabla
        . ($hayDatos ? '' : mail_p('Te escribimos hoy con los datos de la cuenta.', 'font-weight:600;color:#5b21b6'))
        . mail_p('Poné la <b>referencia</b> en el concepto de la transferencia: así identificamos tu pago.', 'font-size:14.5px')
        . '<div style="font:700 13px/1.4 Segoe UI,Arial,sans-serif;letter-spacing:.1em;color:#6d28d9;margin:22px 0 4px">DESPUÉS DE PAGAR</div>'
        . mail_pasos([
            '<b>Respondé este mail</b> con el comprobante.',
            'Te enviamos tu <b>licencia</b> en el día hábil.',
            'Abrí WhisperPRO → <b>Ajustes → Activar Pro</b> y pegá la licencia.',
        ])
        . mail_p('Tenés 10 días corridos para arrepentirte y podés darte de baja cuando quieras. <a href="' . WP_SITIO . 'baja-y-arrepentimiento/" style="color:#6d28d9">Cómo hacerlo</a>.', 'margin-top:24px;font-size:13.5px;color:#6b7280');
    $t = "Hola,\n\nGracias por confirmar tu mail. Para activar WhisperPRO Pro (1 mes), hacé una transferencia con estos datos:\n\nMonto: $monto\n";
    foreach ($filas as [$k, $v]) $t .= "$k: $v\n";
    $t .= "Referencia (ponela en el concepto): $ref\n" . ($hayDatos ? '' : "(Te escribimos hoy con los datos de la cuenta.)\n")
        . "\nCuando transfieras, respondé este mail con el comprobante. Te enviamos tu licencia en el día hábil y la pegás en WhisperPRO → Ajustes → Activar Pro.\n"
        . "Tenés 10 días corridos para arrepentirte: " . WP_SITIO . "baja-y-arrepentimiento/\n\nEl equipo de FESTUDIOS · festudios.pro\n" . WP_EMISOR . ' · ' . WP_DATOS;
    return ['asunto' => 'Datos para pagar WhisperPRO Pro',
            'html' => mail_html('Datos para pagar', 'Referencia ' . $ref . ' · Transferencia bancaria.', $cuerpo, 'Recibís este mail porque confirmaste tu pedido de WhisperPRO Pro.'),
            'texto' => $t];
}
