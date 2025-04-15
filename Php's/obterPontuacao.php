<?php
    $player = 15;
    $pythonPath = "C:\\Users\\bruno\\AppData\\Local\\Programs\\Python\\Python313\\python.exe";  // substituir conforme o caminho `where python`
    $scriptPath = "C:\\Users\\bruno\\PISID_Scripts\\obterPontuacao.py";

    $command = escapeshellcmd("$pythonPath $scriptPath " . escapeshellarg($player));
    $output = shell_exec($command);
    $data = ["resultado" => trim($output)];
    header('Content-Type: application/json');
    echo json_encode($data);
?>