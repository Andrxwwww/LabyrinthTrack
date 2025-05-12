<?php
session_start();

$email = $_POST['Email'];
$password = $_POST['Password'];
$db_name = 'pisid_sql';

try {
    $conn = @new mysqli('localhost', $email, $password, $db_name);
    if ($conn->connect_error) {
        throw new Exception("Email ou password inválidos.");
    }
} catch (Exception $e) {
    header("Location: index.php?error=" . urlencode($e->getMessage()));
    exit();
}

$rootConn = new mysqli('localhost','root','',$db_name);


if ($rootConn -> connect_error){
    die("Erro interno ao verificar utilizador");
}

$smtp = $rootConn -> prepare("SELECT Nome, Grupo FROM utilizador WHERE Email =?");
$smtp->bind_param("s",$email);
$smtp -> execute();
$result = $smtp ->get_result();

if($result ->num_rows == 1){
    $user = $result -> fetch_assoc();
    $_SESSION['db_nome'] = $user['Nome'];
    $_SESSION['db_email'] = $email;
    $_SESSION['db_grupo'] = $user['Grupo'];
    $_SESSION['db_telemovel'] = $user['Telemovel'];
    $_SESSION['db_tipo'] = $user['Tipo'];
    $_SESSION['db_pass'] = $password;
    header("Location: dashboard.php");

}else{
    echo "Utilizador não encontrado";
}


header("Location: dashboard.php");

?>
