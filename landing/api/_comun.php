<?php
/**
 * _comun.php — piezas compartidas de la descarga de WhisperPRO (festudios.pro/whisperpro/api/).
 * Las claves viven en el env.php de la raíz del sitio (nunca en el repo). Acá no se guarda ninguna.
 */
declare(strict_types=1);

require_once dirname(__DIR__, 2) . '/env.php';          // public_html/env.php (define env())
require_once dirname(__DIR__, 2) . '/mail-lib.php';     // smtp_read / smtp_write

const TOKEN_HORAS = 48;

/** Carpeta privada (fuera de public_html): el instalador y el registro de descargas. */
function carpeta_privada(): string {
    return dirname(__DIR__, 3) . '/whisperpro-privado';
}

function secreto(): string {
    return (string)(env('DESCARGA_SECRET') ?: env('LEAD_SECRET') ?: env('SUPABASE_ANON_KEY') ?: 'fe-descarga');
}

function b64u(string $s): string { return rtrim(strtr(base64_encode($s), '+/', '-_'), '='); }
function b64u_dec(string $s): string { return (string)base64_decode(strtr($s, '-_', '+/')); }

/** Token firmado: email + vencimiento. Sin base de datos: se verifica con la firma. */
function crear_token(string $email, int $ahora, string $tipo = 'dl'): string {
    $cuerpo = b64u(json_encode(['e' => $email, 'x' => $ahora + TOKEN_HORAS * 3600, 'k' => $tipo]));
    return $cuerpo . '.' . substr(hash_hmac('sha256', $cuerpo, secreto()), 0, 32);
}

/** Devuelve el email si el token es válido y no venció; si no, null. */
function abrir_token(string $t, int $ahora, string $tipo = 'dl'): ?string {
    $p = explode('.', $t, 2);
    if (count($p) !== 2) return null;
    if (!hash_equals(substr(hash_hmac('sha256', $p[0], secreto()), 0, 32), $p[1])) return null;
    $d = json_decode(b64u_dec($p[0]), true);
    if (!is_array($d) || ($d['x'] ?? 0) < $ahora || !is_string($d['e'] ?? null) || ($d['k'] ?? 'dl') !== $tipo) return null;
    return $d['e'];
}

/** Freno por IP en archivo temporal (la IP no se guarda). */
function freno(string $clave, int $max, int $ventana): bool {
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'x';
    $f = sys_get_temp_dir() . '/fe-wp-' . $clave . '-' . hash('sha256', $ip) . '.txt';
    $ahora = time(); $hits = [];
    if (is_readable($f)) {
        $hits = array_filter(array_map('intval', explode(',', (string)file_get_contents($f))), fn($t) => $t > $ahora - $ventana);
    }
    if (count($hits) >= $max) return false;
    $hits[] = $ahora;
    @file_put_contents($f, implode(',', $hits), LOCK_EX);
    return true;
}

/** Huella de la IP que cambia cada día: sirve para contar visitas distintas sin poder reconstruir la IP. */
function huella_ip(): string {
    return substr(hash_hmac('sha256', ($_SERVER['REMOTE_ADDR'] ?? 'x') . date('Y-m-d'), secreto()), 0, 16);
}

/** Registro de descargas (SQLite, fuera de la carpeta pública). */
function db(): PDO {
    $dir = carpeta_privada();
    if (!is_dir($dir)) @mkdir($dir, 0750, true);
    $pdo = new PDO('sqlite:' . $dir . '/descargas.sqlite');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec('CREATE TABLE IF NOT EXISTS descargas (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, email TEXT, version TEXT, origen TEXT, ip TEXT, ua TEXT)');
    $pdo->exec('CREATE TABLE IF NOT EXISTS fallos_mail (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, email TEXT, que TEXT, detalle TEXT)');
    $pdo->exec('CREATE TABLE IF NOT EXISTS pedidos_pro (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, email TEXT, ref TEXT, usd REAL, ars INTEGER, dolar REAL, estado TEXT)');
    $pdo->exec('CREATE TABLE IF NOT EXISTS solicitudes (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, email TEXT, origen TEXT, dispositivo TEXT, enviado INTEGER)');
    return $pdo;
}

/** Instalador más nuevo en la carpeta privada: [ruta, versión] o null. */
function instalador_actual(): ?array {
    $mejor = null;
    foreach (glob(carpeta_privada() . '/WhisperPRO-Setup-*.exe') ?: [] as $f) {
        if (!preg_match('/Setup-([0-9]+(?:\.[0-9]+)*)\.exe$/', $f, $m)) continue;
        if ($mejor === null || version_compare($m[1], $mejor[1], '>')) $mejor = [$f, $m[1]];
    }
    return $mejor;
}

/** Último error de enviar_a(), para dejarlo en el registro (nunca se le muestra tal cual al visitante). */
$GLOBALS['wp_mail_error'] = '';

/** Mail a una persona (la lib compartida solo manda avisos al equipo). */
function enviar_a(string $para, string $asunto, string $cuerpo): bool {
    $falla = function (string $etapa, string $resp = '') { $GLOBALS['wp_mail_error'] = trim($etapa . ' ' . substr(trim($resp), 0, 160)); return false; };
    $host = env('SMTP_HOST'); $port = (int)env('SMTP_PORT', 587);
    $user = env('SMTP_USER'); $pass = env('SMTP_PASS');
    if (!$host || !$user || !$pass) return $falla('faltan SMTP_HOST/SMTP_USER/SMTP_PASS en env.php');
    $ehlo = strtolower(substr(strrchr($user, '@') ?: '@festudios.pro', 1));
    $s = @stream_socket_client("tcp://$host:$port", $errno, $errstr, 10);
    if (!$s) return $falla("no conecta con $host:$port", $errstr);
    stream_set_timeout($s, 10);
    smtp_read($s); smtp_write($s, 'EHLO ' . $ehlo); smtp_read($s);
    smtp_write($s, 'STARTTLS');
    $r = smtp_read($s);
    if (substr($r, 0, 3) !== '220') { fclose($s); return $falla('STARTTLS', $r); }
    if (!stream_socket_enable_crypto($s, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) { fclose($s); return $falla('TLS'); }
    smtp_write($s, 'EHLO ' . $ehlo); smtp_read($s);
    smtp_write($s, 'AUTH LOGIN'); smtp_read($s);
    smtp_write($s, base64_encode($user)); smtp_read($s);
    smtp_write($s, base64_encode($pass));
    $r = smtp_read($s);
    if (substr($r, 0, 3) !== '235') { fclose($s); return $falla('usuario o clave SMTP rechazados', $r); }
    smtp_write($s, "MAIL FROM:<$user>");
    $r = smtp_read($s);
    if ($r !== '' && $r[0] !== '2') { fclose($s); return $falla('MAIL FROM', $r); }
    smtp_write($s, "RCPT TO:<$para>");
    $r = smtp_read($s);
    if ($r !== '' && $r[0] !== '2') { fclose($s); return $falla('RCPT TO (destinatario rechazado)', $r); }
    smtp_write($s, 'DATA');
    $r = smtp_read($s);
    if (substr($r, 0, 3) !== '354') { fclose($s); return $falla('DATA', $r); }
    $h = [
        'From: WhisperPRO por FESTUDIOS <' . $user . '>',
        'To: <' . $para . '>',
        'Reply-To: <festudioarg@gmail.com>',
        'Subject: =?UTF-8?B?' . base64_encode(clean_header_value($asunto)) . '?=',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Date: ' . date('r'),
    ];
    smtp_write($s, implode("\r\n", $h) . "\r\n\r\n" . preg_replace('/^\./m', '..', $cuerpo) . "\r\n.");
    $r = smtp_read($s);
    smtp_write($s, 'QUIT'); fclose($s);
    if (substr($r, 0, 3) !== '250') return $falla('envío no aceptado', $r);
    return true;
}

/** Deja asentado por qué falló un mail (se ve en estadisticas.php). */
function registrar_fallo(string $email, string $que): void {
    try {
        db()->prepare('INSERT INTO fallos_mail (ts,email,que,detalle) VALUES (?,?,?,?)')
            ->execute([date('c'), $email, $que, (string)($GLOBALS['wp_mail_error'] ?? '')]);
    } catch (Throwable $e) { /* nada */ }
}

function json_salir(int $code, array $data): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

/** Dólar oficial (precio de venta), con caché de una hora. null si no hay dato. */
function cotizacion(): ?array {
    $cache = sys_get_temp_dir() . '/fe-wp-dolar-oficial.json';
    $g = is_readable($cache) ? json_decode((string)file_get_contents($cache), true) : null;
    if (is_array($g) && ($g['t'] ?? 0) > time() - 3600) return $g;
    $ch = curl_init('https://dolarapi.com/v1/dolares/oficial');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 6, CURLOPT_HTTPHEADER => ['Accept: application/json']]);
    $r = json_decode((string)curl_exec($ch), true);
    curl_close($ch);
    if (is_array($r) && is_numeric($r['venta'] ?? null) && $r['venta'] > 100) {
        $out = ['venta' => (float)$r['venta'], 'fecha' => (string)($r['fechaActualizacion'] ?? date('c')), 'fuente' => 'dolarapi.com', 't' => time()];
        @file_put_contents($cache, json_encode($out), LOCK_EX);
        return $out;
    }
    return is_array($g) ? $g : null;
}

function pagina_html(int $code, string $titulo, string $html): void {
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8');
    header('X-Robots-Tag: noindex');
    header('Cache-Control: private, no-store');
    echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' . $titulo . ' — WhisperPRO</title>'
       . '<body style="margin:0;background:#0a0b10;color:#c9ccd8;font:18px/1.6 system-ui,sans-serif"><main style="max-width:600px;margin:9vh auto;padding:0 24px">'
       . '<h1 style="color:#fff;letter-spacing:-.03em">' . $titulo . '</h1>' . $html . '</main>';
    exit;
}
