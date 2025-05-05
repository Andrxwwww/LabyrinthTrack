<?php
// Caminho do ficheiro de log
$logFile = "C:\\xampp\\htdocs\\log_post.txt";

// Escreve o conteúdo do POST no ficheiro de log
file_put_contents($logFile, "=============================\n", FILE_APPEND);
file_put_contents($logFile, "Recebido via POST:\n" . print_r($_POST, true), FILE_APPEND);

// Verifica se os parâmetros foram recebidos
if (isset($_POST['Sala_de_Origem']) && isset($_POST['Sala_de_Destino'])) {
    $doorOrigin = escapeshellarg($_POST['Sala_de_Origem']);
    $doorDestiny = escapeshellarg($_POST['Sala_de_Destino']);

    // Caminho do Python e do script
    $pythonPath = "C:\\Users\\bruno\\AppData\\Local\\Programs\\Python\\Python313\\python.exe";
    $scriptPath = "C:\\Users\\bruno\\PISID_Scripts\\Atuadores\\mqtt_sender.py";

    // Comando a executar
    $command = "$pythonPath $scriptPath --type OpenDoor --room_origin $doorOrigin --room_destiny $doorDestiny";
    file_put_contents($logFile, "Comando executado:\n$command\n", FILE_APPEND);

    // Executa o comando
    $output = shell_exec($command);
    file_put_contents($logFile, "Saída do comando:\n$output\n", FILE_APPEND);

    // Prepara a resposta
    $response = ["status" => "sucesso", "output" => $output];
    file_put_contents($logFile, "Resposta enviada:\n" . print_r($response, true), FILE_APPEND);

    // Envia a resposta JSON para o Android
    header('Content-Type: application/json');
    echo json_encode($response);
} else {
    // Parâmetros inválidos
    $response = ["status" => "erro", "message" => "Parâmetros inválidos. 'Sala_de_Origem' ou 'Sala_de_Destino' não encontrados."];
    file_put_contents($logFile, "Resposta de erro enviada:\n" . print_r($response, true), FILE_APPEND);

    header('Content-Type: application/json');
    echo json_encode($response);
}
?>
