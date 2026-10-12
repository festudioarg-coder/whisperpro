<?php
/**
 * descargar.php?t=<token> — entrega el instalador (que vive fuera de la carpeta pública) y registra la descarga.
 * El token llega por mail (solicitar.php) y vale 48 horas.
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';

function pagina(int $code, string $titulo, string $texto): void {
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8');
    header('X-Robots-Tag: noindex');
    echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' . $titulo . ' — WhisperPRO</title>'
       . '<body style="margin:0;background:#0a0b10;color:#c9ccd8;font:18px/1.6 system-ui,sans-serif"><main style="max-width:560px;margin:12vh auto;padding:0 24px">'
       . '<h1 style="color:#fff;letter-spacing:-.03em">' . $titulo . '</h1><p>' . $texto . '</p>'
       . '<p><a style="color:#c084fc" href="/whisperpro/descargar/">Pedir un link nuevo</a></p></main>';
    exit;
}

$email = abrir_token((string)($_GET['t'] ?? ''), time());
if ($email === null) pagina(403, 'El link venció', 'Los links de descarga duran 48 horas. Pedí uno nuevo y te lo mandamos de nuevo.');
if (!freno('dl', 10, 3600)) pagina(429, 'Demasiados intentos', 'Probá de nuevo en un rato.');

$inst = instalador_actual();
if ($inst === null) pagina(503, 'Todavía no está disponible', 'Estamos terminando de subir el instalador. Probá de nuevo en unos minutos.');
[$ruta, $version] = $inst;

try {
    $st = db()->prepare('INSERT INTO descargas (ts,email,version,origen,ip,ua) VALUES (?,?,?,?,?,?)');
    $st->execute([date('c'), $email, $version, 'mail', huella_ip(), mb_substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 160)]);
} catch (Throwable $e) { /* si falla el registro, igual entregamos */ }

header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="WhisperPRO-Setup-' . $version . '.exe"');
header('Content-Length: ' . filesize($ruta));
header('X-Content-Type-Options: nosniff');
header('Cache-Control: private, no-store');
while (ob_get_level() > 0) ob_end_clean();
readfile($ruta);
exit;
