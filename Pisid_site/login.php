<?php
session_start();
include 'db.php'; 

$userName = "";
$email = $_POST['Email'];
$password = $_POST['Password'];

// Fetch user from new_pisid
$sql = "SELECT * FROM utilizador WHERE Email = ?";
$stmt = $connPisid->prepare($sql);
$stmt->bind_param("s", $email);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $user = $result->fetch_assoc();  
    $userName = $user['Nome'];  
    echo "User Name: " . $userName . "<br>";
} else {
    echo "No user found with that email.";
    exit();
}

// // Fetch user from MySQL system db
// $sqlUser = "SELECT u.User, u.Host, u.Password
//             FROM mysql.db AS d
//             JOIN mysql.user AS u
//             ON d.User = u.User AND d.Host = u.Host
//             WHERE d.db = 'new_pisid' AND u.User = ?";
// $stmtUser = $connMySql->prepare($sqlUser);
// $stmtUser->bind_param("s", $userName);  
// $stmtUser->execute();
// $resultMySql = $stmtUser->get_result();

// if ($resultMySql->num_rows > 0) { 
//     while ($row = $resultMySql->fetch_assoc()) {
//         $storedHashedPassword = $row['Password'];

//         // Check password
//         $query = "SELECT PASSWORD(?) AS hashed_input";
//         $stmtCheck = $connMySql->prepare($query);

//         if ($stmtCheck) {
//             $stmtCheck->bind_param("s", $password); 
//             $stmtCheck->execute();
//             $checkResult = $stmtCheck->get_result();
//             $checkRow = $checkResult->fetch_assoc();
//             $inputPasswordHash = $checkRow['hashed_input']; 
            
//             if ($inputPasswordHash === $storedHashedPassword) {
//                 $_SESSION['name'] = $user['Nome'];
//                 $_SESSION['grupo'] = $user['Grupo'];
//                 header("location: dashboard.php");
//                 exit(); // make sure it stops after redirect
//             } else {
//                 echo "Incorrect password.";  
//             }

//             $stmtCheck->close();
//         } else {
//             echo "Password check query failed.";
//         }
//     }
// } else {
//     echo "No users found in MySQL.";
// }

if ($result->num_rows > 0) {
    $user = $result->fetch_assoc();  

    // Make sure there's a hashed password in DB
    
        $_SESSION['name'] = $user['Nome'];
        $_SESSION['grupo'] = $user['Grupo'];

        header("location: dashboard.php");
        exit();
 
} else {
    echo "No user found with that email.";
}

// Close all remaining statements safely
if (isset($stmt)) $stmt->close();
if (isset($stmtUser)) $stmtUser->close();
?>
