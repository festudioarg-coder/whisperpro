<?php
/**
 * pagar.php?t=<token> — paso 2 de contratar Pro: el mail quedó verificado.
 * Muestra y envía por mail los datos de transferencia (CBU/alias salen del env.php del servidor, nunca del repo),
 * con el monto en pesos al dólar oficial de hoy y un código de referencia. Avisa a FESTUDIOS y registra el pedido.
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';

$email = abrir_token((string)($_GET['t'] ?? ''), time(), 'pro');
if ($email === null) pagina_html(403, 'El link venció', '<p>Los links de confirmación duran 48 horas. Volvé a pedir el plan Pro y te enviamos uno nuevo.</p><p><a style="color:#c084fc" href="/whisperpro/pro/">Contratar WhisperPRO Pro</a></p>');
if (!freno('pago', 10, 3600)) pagina_html(429, 'Demasiados intentos', '<p>Probá de nuevo en un rato.</p>');

const USD = 5.0;
$cot = cotizacion();
$ars = $cot ? (int)(round(USD * $cot['venta'] / 50) * 50) : null;
$ref = 'WP-' . strtoupper(substr(hash_hmac('sha256', $email, secreto()), 0, 6));
$e = fn(string $k) => trim((string)env($k, ''));
$cbu = $e('PAGO_CBU'); $alias = $e('PAGO_ALIAS'); $titular = $e('PAGO_TITULAR'); $cuit = $e('PAGO_CUIT'); $banco = $e('PAGO_BANCO');
$hayDatos = ($cbu !== '' || $alias !== '');

$monto = $ars !== null
    ? '$' . number_format($ars, 0, ',', '.') . ' ARS (US$ 5 al dólar oficial vendedor de hoy: $' . number_format($cot['venta'], 2, ',', '.') . ')'
    : 'US$ 5 en pesos al dólar oficial del día (te confirmamos el monto exacto por mail)';

$datos = $hayDatos
    ? "Monto: $monto\n" . ($titular !== '' ? "Titular: $titular\n" : '') . ($cuit !== '' ? "CUIT: $cuit\n" : '')
      . ($banco !== '' ? "Banco: $banco\n" : '') . ($cbu !== '' ? "CBU: $cbu\n" : '') . ($alias !== '' ? "Alias: $alias\n" : '')
      . "Referencia (ponela en el concepto): $ref"
    : "Monto: $monto\nReferencia: $ref\n(Te escribimos en el día con los datos de la cuenta.)";

$nuevo = true;
try {
    $pdo = db();
    $st = $pdo->prepare("SELECT COUNT(*) FROM pedidos_pro WHERE email=? AND ts > ?");
    $st->execute([$email, date('c', time() - 86400)]);
    $nuevo = (int)$st->fetchColumn() === 0;
    if ($nuevo) $pdo->prepare('INSERT INTO pedidos_pro (ts,email,ref,usd,ars,dolar,estado) VALUES (?,?,?,?,?,?,?)')
        ->execute([date('c'), $email, $ref, USD, $ars, $cot['venta'] ?? null, 'datos_enviados']);
} catch (Throwable $x) { /* el registro no debe frenar la entrega */ }

if ($nuevo) {   // una sola vez por día por mail, aunque abran el link varias veces
    $filasPago = [];
    foreach ([['Titular', $titular, false], ['CUIT', $cuit, false], ['Banco', $banco, false], ['CBU', $cbu, true], ['Alias', $alias, true]] as $f) if ($f[1] !== '') $filasPago[] = $f;
    $m = mail_datos_pago($monto, $ref, $filasPago, $hayDatos);
    $okMail = enviar_a($email, $m['asunto'], $m['texto'], $m['html']);
    if (!$okMail) registrar_fallo($email, 'pro-datos-de-pago');
    if (function_exists('send_notification_mail')) {
        @send_notification_mail('[FE · WhisperPRO Pro] Mail verificado: ' . $email,
            "Verificó su mail y se le enviaron los datos de pago.\n\nMail: $email\nReferencia: $ref\nMonto: $monto\n\n"
            . "Cuando llegue el comprobante: python herramientas/licencias.py emitir --email $email --dias 30",
            $email);
    }
}

$html = '<p style="color:#34e0a1"><b>Listo, tu mail está confirmado.</b></p>'
      . '<p>Estos son los datos para transferir. También te los enviamos por mail.</p>'
      . '<div style="background:#11131a;border:1px solid #1b1e29;border-radius:18px;padding:18px 24px;margin:18px 0;white-space:pre-line;font:16px/1.7 ui-monospace,monospace;color:#e9eaf2">' . htmlspecialchars($datos) . '</div>'
      . '<p>Cuando transfieras, respondé el mail con el comprobante y te enviamos la licencia. Se activa en WhisperPRO → Ajustes → Activar Pro.</p>';
pagina_html(200, 'Datos para pagar', $html);
