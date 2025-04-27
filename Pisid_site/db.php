<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "new_pisid";

$connPisid = new mysqli($servername, $username, $password, $dbname);
$connMySql = new mysqli($servername, $username, $password, "mysql");
// Check connection
if ($connPisid->connect_error || $connMySql->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

?>