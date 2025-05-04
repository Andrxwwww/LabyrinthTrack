<?php
    $servername = "localhost";
    $username = "root";  
    $password = "";  
    $dbname = "mysql_sql";  
    
    $conn = new mysqli($servername, $username, $password, $dbname);
    
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT u.User, u.Host, u.Password
        FROM mysql.db AS d
        JOIN mysql.user AS u
        ON d.User = u.User AND d.Host = u.Host
        WHERE d.db = 'pisid'; "; // For MariaDB, use 'password' column
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    echo "MySQL Users and their Password Hashes:<br>";

    // Loop through each row and display the columns
    while ($row = $result->fetch_assoc()) {
        echo "User: " . $row['User'] . " - Host: " . $row['Host'] ." - Password" .$row['Password']  . "<br>";
    }
} else {
    echo "No users found.";
}

$conn->close();

?>