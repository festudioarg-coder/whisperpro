<?php
/**
 * dolar.php — cotización del dólar oficial (precio de venta) para mostrar el plan Pro en pesos.
 * La consulta a dolarapi.com la hace el servidor y se guarda una hora (ver cotizacion() en _comun.php):
 * los visitantes no hablan con ningún tercero. GET → { venta, fecha, fuente }
 */
declare(strict_types=1);
require_once __DIR__ . '/_comun.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=900');
$c = cotizacion();
if ($c === null) { http_response_code(503); echo json_encode(['error' => 'sin cotización']); exit; }
echo json_encode(['venta' => $c['venta'], 'fecha' => $c['fecha'], 'fuente' => $c['fuente']]);
