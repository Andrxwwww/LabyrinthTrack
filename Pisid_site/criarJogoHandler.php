<?php
session_start();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_SESSION['db_email'];
    $password = $_SESSION['db_pass'];
    $grupo = $_SESSION['db_grupo'];
    $descricao = $_POST['descricao'];
    $dbname = "pisid_sql";
    $conn = new mysqli("localhost", $username, $password, $dbname);
    if ($conn->connect_error) {
        die("Erro na ligação: " . $conn->connect_error);
    }

    $stmt = $conn->prepare("CALL Criar_jogo(?)");
    $stmt->bind_param("s", $descricao);

    if ($stmt->execute()) {
        header("Location: dashboard.php");
    } else {
        echo "Erro ao criar jogo: " . $stmt->error;
    }

    $stmt->close();
    $conn->close();
}
?>