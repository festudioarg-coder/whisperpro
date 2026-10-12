<?php
/**
 * estadisticas.php?k=<WHISPERPRO_STATS_KEY> — descargas y solicitudes de WhisperPRO (solo para FESTUDIOS).
 * La clave se define en env.php; sin ella, o con otra, no muestra nada. &json=1 devuelve JSON.
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';
header('X-Robots-Tag: noindex');
$clave = (string)env('WHISPERPRO_STATS_KEY');
if ($clave === '' || !hash_equals($clave, (string)($_GET['k'] ?? ''))) { http_response_code(404); exit; }

$pdo = db();
$q = fn(string $sql) => $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
$d = [
    'totales' => $q("SELECT (SELECT COUNT(*) FROM solicitudes) AS solicitudes, (SELECT COUNT(DISTINCT email) FROM solicitudes) AS mails_distintos, (SELECT COUNT(*) FROM descargas) AS descargas, (SELECT COUNT(DISTINCT email) FROM descargas) AS personas_que_bajaron")[0],
    'por_dia' => $q("SELECT substr(ts,1,10) AS dia, COUNT(*) AS descargas FROM descargas GROUP BY dia ORDER BY dia DESC LIMIT 30"),
    'solicitudes_por_dia' => $q("SELECT substr(ts,1,10) AS dia, COUNT(*) AS solicitudes, SUM(dispositivo='celular') AS desde_celular FROM solicitudes GROUP BY dia ORDER BY dia DESC LIMIT 30"),
    'por_version' => $q("SELECT version, COUNT(*) AS descargas FROM descargas GROUP BY version ORDER BY version DESC"),
    'pedidos_pro' => $q("SELECT ts, email, ref, ars, estado FROM pedidos_pro ORDER BY id DESC LIMIT 30"),
    'fallos_de_mail' => $q("SELECT ts, email, que, detalle FROM fallos_mail ORDER BY id DESC LIMIT 20"),
    'sin_mail_enviado' => $q("SELECT ts, email FROM solicitudes WHERE enviado=0 ORDER BY id DESC LIMIT 20"),
];
if (isset($_GET['json'])) { header('Content-Type: application/json; charset=utf-8'); echo json_encode($d, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT); exit; }

header('Content-Type: text/html; charset=utf-8');
function tabla(array $filas): string {
    if (!$filas) return '<p>Sin datos todavía.</p>';
    $h = '<table><tr>' . implode('', array_map(fn($c) => '<th>' . htmlspecialchars((string)$c) . '</th>', array_keys($filas[0]))) . '</tr>';
    foreach ($filas as $f) $h .= '<tr>' . implode('', array_map(fn($v) => '<td>' . htmlspecialchars((string)$v) . '</td>', $f)) . '</tr>';
    return $h . '</table>';
}
echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>WhisperPRO · estadísticas</title>'
   . '<style>body{background:#0a0b10;color:#c9ccd8;font:15px/1.5 system-ui;margin:0;padding:24px;max-width:900px}h1,h2{color:#fff}table{border-collapse:collapse;margin:8px 0 28px}th,td{border-bottom:1px solid #1b1e29;padding:6px 14px;text-align:left}th{color:#8b92a8}</style>'
   . '<h1>WhisperPRO · descargas</h1><h2>Totales</h2>' . tabla([$d['totales']])
   . '<h2>Descargas por día</h2>' . tabla($d['por_dia']) . '<h2>Solicitudes por día</h2>' . tabla($d['solicitudes_por_dia'])
   . '<h2>Pedidos de Pro (mail verificado)</h2>' . tabla($d['pedidos_pro']) . '<h2>Por versión</h2>' . tabla($d['por_version']) . '<h2>Por qué fallaron los mails</h2>' . tabla($d['fallos_de_mail']) . '<h2>Mails que no se pudieron enviar</h2>' . tabla($d['sin_mail_enviado']);
