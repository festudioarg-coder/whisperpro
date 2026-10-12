<?php
/**
 * contratar.php — pide contratar WhisperPRO Pro.
 * POST { email, consentimiento:true }  →  { ok:true }
 * Paso 1: guarda el contacto en la Bandeja del CRM y manda un mail con un link de verificación (48 h).
 * Los datos de pago NO se muestran acá: salen recién cuando la persona confirma que el mail es suyo (pagar.php).
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') json_salir(405, ['error' => 'Method not allowed']);
$in = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($in)) json_salir(400, ['error' => 'JSON inválido']);
if (!freno('pro', 5, 3600)) json_salir(429, ['error' => 'Demasiados pedidos. Probá en un rato.']);

$email = strtolower(trim((string)($in['email'] ?? '')));
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 120) json_salir(400, ['error' => 'Revisá el mail.']);
if (empty($in['consentimiento'])) json_salir(400, ['error' => 'Falta aceptar el consentimiento.']);

$url = env('SUPABASE_URL'); $key = env('SUPABASE_ANON_KEY');
if ($url && $key) {
    $ch = curl_init(rtrim($url, '/') . '/rest/v1/form_submissions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_CUSTOMREQUEST => 'POST', CURLOPT_TIMEOUT => 8,
        CURLOPT_POSTFIELDS => json_encode([
            'form_type' => 'rapido',
            'name'      => 'Quiere WhisperPRO Pro',
            'email'     => $email,
            'message'   => 'Pidió contratar WhisperPRO Pro (US$ 5/mes) el ' . date('d/m/Y H:i') . '. Todavía no verificó el mail. Aceptó recibir novedades.',
            'status'    => 'new',
        ], JSON_UNESCAPED_UNICODE),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'apikey: ' . $key, 'Authorization: Bearer ' . $key, 'Prefer: return=minimal'],
    ]);
    curl_exec($ch); curl_close($ch);
}

$link = 'https://festudios.pro/whisperpro/api/pagar.php?t=' . crear_token($email, time(), 'pro');
$m = mail_verificacion_pro($link);
$enviado = enviar_a($email, $m['asunto'], $m['texto'], $m['html']);
if (!$enviado) registrar_fallo($email, 'pro-verificacion');
json_salir(200, ['ok' => true, 'enviado' => $enviado]);
