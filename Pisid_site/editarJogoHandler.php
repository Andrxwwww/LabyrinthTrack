<?php
session_start();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    var_dump($_POST);
    if (!isset($_POST['id_jogo'], $_POST['descricao'])) {
        die("Dados insuficientes para atualizar o jogo.");
    }

    $idJogo = $_POST['id_jogo'];
    $descricao = $_POST['descricao'];

    if (empty($descricao)) {
        die("A descrição não pode ser vazia.");
    }

    $username = $_SESSION['db_email'];
    $password = $_SESSION['db_pass'];
    $dbname = "pisid_sql";

    $conn = new mysqli("localhost", $username, $password, $dbname);
    if ($conn->connect_error) {
        die("Erro na ligação: " . $conn->connect_error);
    }

    $stmt = $conn->prepare("CALL Alterar_jogo(?, ?)");
    $stmt->bind_param("is", $idJogo, $descricao);

    if ($stmt->execute()) {

        header("Location: dashboard.php");
        exit();
    } else {
        echo "Erro ao editar jogo: " . $conn->error;
    }

    $stmt->close();
    $conn->close();
}
?>
