<?php
/**
 * enviar-link.php?k=<WHISPERPRO_STATS_KEY>&email=<mail> — reenvía el mail de descarga (HTML) a una persona, con copia oculta a FESTUDIOS.
 * Solo para el equipo: sin la clave correcta no existe (404). Sirve para ayudar a quien no recibió el mail.
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';
header('X-Robots-Tag: noindex');

$clave = (string)env('WHISPERPRO_STATS_KEY');
if ($clave === '' || !hash_equals($clave, (string)($_GET['k'] ?? ''))) { http_response_code(404); exit; }

$email = strtolower(trim((string)($_GET['email'] ?? '')));
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 120) {
    pagina_html(400, 'Falta el mail', '<p>Usá <code>?k=…&amp;email=persona@mail.com</code></p>');
}

$link = 'https://festudios.pro/whisperpro/api/descargar.php?t=' . crear_token($email, time());
$m = mail_descarga($link);
$ok = enviar_a($email, $m['asunto'], $m['texto'], $m['html']);
try {
    db()->prepare('INSERT INTO solicitudes (ts,email,origen,dispositivo,enviado,respuesta) VALUES (?,?,?,?,?,?)')
        ->execute([date('c'), $email, 'reenvio-manual', '', $ok ? 1 : 0, $ok ? $GLOBALS['wp_mail_resp'] : $GLOBALS['wp_mail_error']]);
} catch (Throwable $e) { /* nada */ }
if (!$ok) registrar_fallo($email, 'reenvio-manual');

pagina_html($ok ? 200 : 502, $ok ? 'Mail enviado' : 'No se pudo enviar',
    $ok ? '<p>Se envió el mail de descarga a <b>' . htmlspecialchars($email) . '</b> con copia oculta a FESTUDIOS (festudioarg@gmail.com).</p><p>Respuesta del servidor de mail: <code>' . htmlspecialchars((string)$GLOBALS['wp_mail_resp']) . '</code></p>'
        : '<p>El servidor de mail no lo aceptó: <code>' . htmlspecialchars((string)$GLOBALS['wp_mail_error']) . '</code></p>');
