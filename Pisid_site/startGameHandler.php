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
$scriptPath = escapeshellarg("C:\\Code\\run.py");

$pythonPath = "C:\\Users\\bruno\\AppData\\Local\\Programs\\Python\\Python313\\python.exe";
$scriptPath = "C:\\Code\\run.py";
$logFile = "C:\\xampp\\htdocs\\Pisid_site\\python_log.txt";


// Conectar à base de dados
$conn = new mysqli("localhost", $username, $password, $dbname);
if ($conn->connect_error) {
    die("Falha na conexão: " . $conn->connect_error);
}


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
// Comando para rodar o script em background e registrar o log
$output = shell_exec("whoami");
echo "<pre>Utilizador do Apache: $output</pre>";

$pythonPath = "C:\\Users\\bruno\\AppData\\Local\\Programs\\Python\\Python313\\python.exe";
$scriptPath = "C:\\Users\\bruno\\PISID_Scripts\\Code\\run.py";

$command = "\"$pythonPath\" \"$scriptPath\"";
$output = shell_exec($command . " 2>&1");
echo "<pre>Output do Python:\n$output</pre>";

// Redireciona de volta para o dashboard
header("Location: dashboard.php");
exit;
?>
