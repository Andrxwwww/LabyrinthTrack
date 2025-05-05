<?php
header('Content-Type: application/json');

// Obter hora atual no formato YYYY-MM-DD HH:MM:SS
$now = new DateTime("now", new DateTimeZone("GMT"));// ou GMT se preferires
$currentHour = $now->format('Y-m-d H:i:s');

// Simular valores
$soundValue = 18;
$normalNoise = 19.00;

// Criar estrutura de dados
$data = [
    [
        "Hour" => "2025-04-26 15:00:57.000",
        "Sound" => (string)19,
        "normalnoise" => number_format($normalNoise, 2, '.', '')
    ],
    [
        "Hour" => "2025-04-26 15:36:57.000",
        "Sound" => (string)$soundValue,
        "normalnoise" => number_format($normalNoise, 2, '.', '')
    ],
    [
        "Hour" => "2025-04-26 15:38:57.000",
        "Sound" => (string)$soundValue,
        "normalnoise" => number_format($normalNoise, 2, '.', '')
    ],
];

// Devolver JSON
echo json_encode($data);
?>