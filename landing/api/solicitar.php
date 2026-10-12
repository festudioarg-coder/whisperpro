<?php
/**
 * solicitar.php — pide el link de descarga de WhisperPRO.
 * POST { email, consentimiento:true, origen?, dispositivo? }  →  { ok:true }
 * Guarda el contacto en la Bandeja del CRM (form_submissions), registra la solicitud y manda al mail un link
 * firmado que vale 48 horas. Responde { ok, enviado }: enviado=false si el servidor de mail no pudo mandarlo (queda registrado el motivo).
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') json_salir(405, ['error' => 'Method not allowed']);
$in = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($in)) json_salir(400, ['error' => 'JSON inválido']);
if (!freno('sol', 5, 3600)) json_salir(429, ['error' => 'Demasiados pedidos. Probá en un rato.']);

$email = strtolower(trim((string)($in['email'] ?? '')));
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 120) json_salir(400, ['error' => 'Revisá el mail.']);
if (empty($in['consentimiento'])) json_salir(400, ['error' => 'Falta aceptar el consentimiento.']);
$origen = mb_substr(trim((string)($in['origen'] ?? 'descarga')), 0, 40);
$disp = in_array($in['dispositivo'] ?? '', ['celular', 'compu'], true) ? $in['dispositivo'] : '';

/* 1) Lead en la Bandeja del CRM (misma tabla que lead-rapido.php) */
$url = env('SUPABASE_URL'); $key = env('SUPABASE_ANON_KEY');
if ($url && $key) {
    $ch = curl_init(rtrim($url, '/') . '/rest/v1/form_submissions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_CUSTOMREQUEST => 'POST', CURLOPT_TIMEOUT => 8,
        CURLOPT_POSTFIELDS => json_encode([
            'form_type' => 'rapido',
            'name'      => 'Descargó WhisperPRO',
            'email'     => $email,
            'message'   => 'Pidió el link de descarga de WhisperPRO (' . date('d/m/Y H:i') . ')'
                . ($disp !== '' ? " desde la $disp" : '') . ". Aceptó recibir novedades. Origen: $origen.",
            'status'    => 'new',
        ], JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'apikey: ' . $key, 'Authorization: Bearer ' . $key, 'Prefer: return=minimal'],
    ]);
    curl_exec($ch); curl_close($ch);
}

/* 2) Link firmado por mail */
$link = 'https://festudios.pro/whisperpro/api/descargar.php?t=' . crear_token($email, time());
$cuerpo = "Hola,\n\nGracias por probar WhisperPRO. Este es tu link de descarga (vale 48 horas):\n\n$link\n\n"
    . "Para Windows 10 y 11. Si Windows muestra «Windows protegió su PC», tocá «Más información» y después «Ejecutar de todas formas»: es normal en aplicaciones nuevas.\n\n"
    . "Al abrirlo te guiamos para conectar tu clave gratuita de IA en un minuto.\n\n"
    . "¿Dudas? Respondé este mail.\n\nFESTUDIOS · festudios.pro\n\n"
    . "Recibís este mail porque pediste la descarga en festudios.pro/whisperpro. Para borrar tus datos o no recibir más novedades, respondé con la palabra BAJA.";
$enviado = enviar_a($email, 'Tu descarga de WhisperPRO', $cuerpo);
if (!$enviado) registrar_fallo($email, 'descarga');

try {
    $st = db()->prepare('INSERT INTO solicitudes (ts,email,origen,dispositivo,enviado) VALUES (?,?,?,?,?)');
    $st->execute([date('c'), $email, $origen, $disp, $enviado ? 1 : 0]);
} catch (Throwable $e) { /* el registro no debe frenar la entrega */ }

json_salir(200, ['ok' => true, 'enviado' => $enviado]);
