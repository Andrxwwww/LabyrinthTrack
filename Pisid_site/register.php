<?php
include 'db.php'; 
$Name = $_POST['Nome'];
$Email = $_POST['Email'];
$Telemovel = $_POST['Telemovel'];
$Tipo = $_POST['Tipo'];
$Grupo = $_POST['Grupo'];
$password = password_hash($_POST["Password"], PASSWORD_DEFAULT);


$sql = "INSERT INTO utilizador (Nome,Telemovel,Tipo,Grupo,Email) values (?,?,?,?,?)";
$stmt = $connPisid->prepare($sql);
$stmt->bind_param("sssis", $Name, $Telemovel, $Tipo, $Grupo, $Email);
if ($stmt->execute()) {
    echo "Registration successful!";
    header("location:dashboard.php");
} else {
    echo "Error: " . $stmt->error;
}

$stmt->close();
?>