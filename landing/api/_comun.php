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
function crear_token(string $email, int $ahora): string {
    $cuerpo = b64u(json_encode(['e' => $email, 'x' => $ahora + TOKEN_HORAS * 3600]));
    return $cuerpo . '.' . substr(hash_hmac('sha256', $cuerpo, secreto()), 0, 32);
}

/** Devuelve el email si el token es válido y no venció; si no, null. */
function abrir_token(string $t, int $ahora): ?string {
    $p = explode('.', $t, 2);
    if (count($p) !== 2) return null;
    if (!hash_equals(substr(hash_hmac('sha256', $p[0], secreto()), 0, 32), $p[1])) return null;
    $d = json_decode(b64u_dec($p[0]), true);
    if (!is_array($d) || ($d['x'] ?? 0) < $ahora || !is_string($d['e'] ?? null)) return null;
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

/** Mail a una persona (la lib compartida solo manda avisos al equipo). Copia oculta a FESTUDIOS. */
function enviar_a(string $para, string $asunto, string $cuerpo): bool {
    $host = env('SMTP_HOST'); $port = (int)env('SMTP_PORT', 587);
    $user = env('SMTP_USER'); $pass = env('SMTP_PASS');
    if (!$host || !$user || !$pass) return false;
    $ehlo = strtolower(substr(strrchr($user, '@') ?: '@festudios.pro', 1));
    $s = @stream_socket_client("tcp://$host:$port", $errno, $errstr, 10);
    if (!$s) return false;
    stream_set_timeout($s, 10);
    smtp_read($s); smtp_write($s, 'EHLO ' . $ehlo); smtp_read($s);
    smtp_write($s, 'STARTTLS');
    if (substr(smtp_read($s), 0, 3) !== '220') { fclose($s); return false; }
    if (!stream_socket_enable_crypto($s, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) { fclose($s); return false; }
    smtp_write($s, 'EHLO ' . $ehlo); smtp_read($s);
    smtp_write($s, 'AUTH LOGIN'); smtp_read($s);
    smtp_write($s, base64_encode($user)); smtp_read($s);
    smtp_write($s, base64_encode($pass));
    if (substr(smtp_read($s), 0, 3) !== '235') { fclose($s); return false; }
    smtp_write($s, "MAIL FROM:<$user>"); smtp_read($s);
    smtp_write($s, "RCPT TO:<$para>"); smtp_read($s);
    smtp_write($s, 'DATA'); smtp_read($s);
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
    $ok = substr(smtp_read($s), 0, 3) === '250';
    smtp_write($s, 'QUIT'); fclose($s);
    return $ok;
}

function json_salir(int $code, array $data): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}
