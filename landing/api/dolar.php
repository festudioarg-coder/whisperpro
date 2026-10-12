<?php
/**
 * dolar.php — cotización del dólar para mostrar el precio del plan Pro en pesos.
 * Lee dolarapi.com (dólar oficial, precio de venta) y la guarda una hora, así los visitantes no consultan a un tercero
 * ni se pasa del límite de pedidos. Si el servicio cae, usa la última cotización guardada.
 * GET → { venta, fecha, fuente }
 */
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=900');
const CASA = 'oficial';   // 'oficial' | 'blue' | 'bolsa' (MEP)
$cache = sys_get_temp_dir() . '/fe-wp-dolar-' . CASA . '.json';

$guardado = is_readable($cache) ? json_decode((string)file_get_contents($cache), true) : null;
if (is_array($guardado) && ($guardado['t'] ?? 0) > time() - 3600) { unset($guardado['t']); echo json_encode($guardado); exit; }

$ch = curl_init('https://dolarapi.com/v1/dolares/' . CASA);
curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 6, CURLOPT_HTTPHEADER => ['Accept: application/json']]);
$r = json_decode((string)curl_exec($ch), true);
curl_close($ch);

if (is_array($r) && is_numeric($r['venta'] ?? null) && $r['venta'] > 100) {
    $out = ['venta' => (float)$r['venta'], 'fecha' => (string)($r['fechaActualizacion'] ?? date('c')), 'fuente' => 'dolarapi.com'];
    @file_put_contents($cache, json_encode($out + ['t' => time()]), LOCK_EX);
    echo json_encode($out); exit;
}
if (is_array($guardado)) { unset($guardado['t']); echo json_encode($guardado); exit; }
http_response_code(503);
echo json_encode(['error' => 'sin cotización']);
