<?php 

file_put_contents("C:\\xampp\\htdocs\\log_post.txt", "Recebido via POST:\n" . print_r($_POST, true), FILE_APPEND);
$doorOrigin = escapeshellarg($_POST["Sala:"]);
$pythonPath = escapeshellarg("C:\\Users\\bruno\\AppData\\Local\\Programs\\Python\\Python313\\python.exe");
$scriptPath = escapeshellarg("C:\\Users\\bruno\\PISID_Scripts\\Atuadores\\mqtt_sender.py");

$command = "$pythonPath $scriptPath --type Score --room $doorOrigin";

$output = shell_exec($command);

header('Content-Type: application/json');
echo json_encode(["output" => $output]);
?>