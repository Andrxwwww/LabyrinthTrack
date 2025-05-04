<?php
session_start();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_SESSION['db_email'];
    $password = $_SESSION['db_pass'];
    $grupo = $_SESSION['db_grupo'];
    $descricao = $_POST['descricao'];

    $conn = new mysqli("localhost", $username, $password, "pisid");

    if ($conn->connect_error) {
        die("Ligação falhou: " . $conn->connect_error);
    }

    $sql = "call StartGame($descricao)";
    $result = mysqli_query($conn, $sql);
    if ($result) {
        // success: redirect or message
        echo "111111111111";// or wherever you want
        exit();
    } else {
        echo "Erro ao criar jogo: " . $stmt->error;
    }

    $stmt->close();
    $conn->close();
}
?>