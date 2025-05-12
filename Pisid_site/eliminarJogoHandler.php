<?php
session_start();

if (!isset($_POST['id_jogo'])) {
    die("ID do jogo não foi enviado.");
}

$idJogo = $_POST['id_jogo'];

$username = $_SESSION['db_email'];
$password = $_SESSION['db_pass'];
$dbname = "pisid_sql";
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT); 

try{
    $conn = new mysqli("localhost", $username, $password, $dbname);
    $conn->set_charset("utf8mb4");
    if ($conn->connect_error) {
        die("Erro na ligação: " . $conn->connect_error);
    }
    
$stmt = $conn->prepare("CALL Eliminar_Jogo(?)");
$stmt->bind_param("i", $idJogo);
$stmt->execute();
$stmt->close();
$conn->close();
header("Location: dashboard.php");
exit();
}catch(mysqli_sql_exception $e){
    $errorMessage = urlencode($e->getMessage());
    header("Location: dashboard.php?error=$errorMessage");
    exit();
}

?>