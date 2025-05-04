<?php
session_start();

if (!isset($_POST['id_jogo'])) {
    die("ID do jogo não foi enviado.");
}

$idJogo = $_POST['id_jogo'];

$username = $_SESSION['db_email'];
$password = $_SESSION['db_pass'];
$dbname = "pisid_sql";

$conn = new mysqli("localhost", $username, $password, $dbname);
if ($conn->connect_error) {
    die("Erro na ligação: " . $conn->connect_error);
}

// Prepare and execute stored procedure
$stmt = $conn->prepare("CALL EliminateGame(?)");
$stmt->bind_param("i", $idJogo);

if ($stmt->execute()) {
    header("Location: dashboard.php"); // redirect after success
    exit();
} else {
    echo "Erro ao eliminar jogo: " . $conn->error;
}

$stmt->close();
$conn->close();
?>