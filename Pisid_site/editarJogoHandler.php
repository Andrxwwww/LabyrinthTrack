<?php
session_start();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['id_jogo'], $_POST['descricao'])) {
        die("Dados insuficientes para atualizar o jogo.");
    }

    $idJogo = $_POST['id_jogo'];
    $descricao = $_POST['descricao'];
    $spamTol = isset($_POST['spamTol']) ? $_POST['spamTol'] : null;

    if (empty($descricao)) {
        die("A descrição não pode ser vazia.");
    }

    // Prepare the JSON data to send to the stored procedure
    $data = array(
        'Descricao' => $descricao,
        'spamTol' => $spamTol
    );
    $jsonData = json_encode($data);

    $username = $_SESSION['db_email'];
    $password = $_SESSION['db_pass'];
    $dbname = "pisid_sql";

    mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);

    try {
        $conn = new mysqli("localhost", $username, $password, $dbname);
        $conn->set_charset("utf8mb4");

        // Prepare the call to the stored procedure
        $stmt = $conn->prepare("CALL Alterar_jogo_JSON(?, ?)");
        $stmt->bind_param("is", $idJogo, $jsonData); // Bind the id and JSON data

        $stmt->execute();

        $stmt->close();
        $conn->close();

        header("Location: dashboard.php");
        exit();
    } catch (mysqli_sql_exception $e) {
        $errorMessage = urlencode($e->getMessage());
        header("Location: dashboard.php?error=$errorMessage");
        exit();
    }
}
?>
