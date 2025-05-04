<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "pisid_sql";

$connPisid = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($connPisid->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

?>