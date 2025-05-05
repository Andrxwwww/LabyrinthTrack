<?php
// Comando para executar o script .bat
$command = "C:\\Users\\bruno\\Desktop\\pisidtraba\\versao2\\run.bat";

// Executa o comando sem bloquear o PHP
shell_exec('start "" cmd /k "' . $command . '"');

// Opcionalmente retorna algo ao browser
echo json_encode(["status" => "Comando enviado para terminal."]);
?>