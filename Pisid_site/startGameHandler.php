<?php
session_start();

// Verifica se a sessão está válida e se o ID do jogo foi fornecido
if (!isset($_SESSION['db_email']) || !isset($_GET['id'])) {
    die("Sessão inválida ou ID do jogo em falta.");
}

$username = $_SESSION['db_email'];
$password = $_SESSION['db_pass'];
$dbname = "pisid_sql";
$idJogo = intval($_GET['id']);  // Corrigido para 'id' com letra minúscula (vindo do GET)
$scriptPath = escapeshellarg("C:/Users/Rafael/Documents/GitHub/PISID_Scripts/Code/run.py");

// Conectar à base de dados
$conn = new mysqli("localhost", $username, $password, $dbname);
if ($conn->connect_error) {
    die("Falha na conexão: " . $conn->connect_error);
}

// Atualizar estado do jogo para "running"
$updateStmt = $conn->prepare("UPDATE jogo SET Estado = 'running' WHERE IDJogo = ?");
$updateStmt->bind_param("i", $idJogo);
if (!$updateStmt->execute()) {
    die("Erro ao atualizar estado do jogo: " . $updateStmt->error);
}
$updateStmt->close();

// Executar procedure para iniciar o jogo
$stmt = $conn->prepare("CALL Correr_Jogo(?)");
$stmt->bind_param("i", $idJogo);
if (!$stmt->execute()) {
    die("Erro ao iniciar o jogo: " . $stmt->error);
}
$stmt->close();

// Liberta a sessão para não bloquear futuras requisições
session_write_close();

// Executa o script Python em background (Windows)
pclose(popen("start /B python $scriptPath", "r"));

// Redireciona de volta para o dashboard
header("Location: dashboard.php");
exit;
?>
