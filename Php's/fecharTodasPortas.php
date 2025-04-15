<?php
    $pythonPath = "C:\\Users\\bruno\\AppData\\Local\\Programs\\Python\\Python313\\python.exe";  // Caminho para o Python
    $scriptPath = "C:\\Users\\bruno\\PISID_Scripts\\Atuadores\\mqtt_sender.py"; // Caminho para o script Python

    $command = escapeshellcmd("$pythonPath $scriptPath --type CloseAllDoor");

    $output = shell_exec($command);

    header('Content-Type: application/json');
    echo json_encode(["output" => $output]);
?>