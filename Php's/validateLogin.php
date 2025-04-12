<?php 
$db = "pisid_sql";
$dbhost = "localhost";
$return = ["message" => "", "success" => false];
$username = $_POST["username"] ?? '';
$password = $_POST["password"] ?? '';

// Tenta conectar ao MySQL
$conn = mysqli_connect($dbhost, $username, $password);

if ($conn) {
    // Verifica se o usuário tem acesso ao banco 'pisid_sql'
    $checkDB = mysqli_select_db($conn, $db);
    
    if ($checkDB) {
        $return["success"] = true;
        $return["message"] = "Login válido!";
    } else {
        $return["message"] = "Usuário não tem acesso ao banco de dados.";
    }
    
    mysqli_close($conn);
} else {
    $return["message"] = "Credenciais inválidas ou erro de conexão.";
}

header('Content-Type: application/json');
echo json_encode($return);
?>