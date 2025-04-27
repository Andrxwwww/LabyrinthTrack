<?php
session_start();
include 'db.php';

$sql = "SELECT * FROM jogo WHERE jogador=?";
$stmt = $connPisid->prepare($sql);
$stmt->bind_param("i", $_SESSION['grupo']);
$stmt->execute();
$result = $stmt->get_result();

$jogos = $result->fetch_all(MYSQLI_ASSOC);
$stmt->close();
?>


<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1.0"
    />
    <title>Pisid</title>
    <link
      href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="style.css" />
  </head>
  <body id="dashboard" style="overflow: hidden;">
    <div class="dashboard-container" style="height:20vh">
            <div class="dashboard-header">
                <div class="dashboard-username"><h1>Utilizador: <?php echo $_SESSION['name']; ?></h1></div>
            <div class="dashboard-search">
                <input placeholder="Pesquisar jogo"/>
            </div>
            <div class="dashboard-logout">
                <button><i class='bx bxs-door-open'></i></button>
            </div>
        </div>
            <div class="" style="background-color:white;margin:40px 70px;padding:30px;border-radius:30px;">
                <div><h1>Criar um jogo novo:</h1></div>
                <div style="margin-top:60px;">
                    <p style="font-size:30px;">IdJogo: 4</p>
                    <div style="display: flex;justify-content:start;align-items:center;margin-top:30px;">
                        <label style="font-size:30px;margin-right:10px;">Descrição:</label>
                        <textarea name="descricao" id="descricao" cols="100" rows="4" placeholder=""></textarea>
                    </div>
                    <div style="font-size: 30px;margin-top:30px;">Data e Hora: 2025-03-20 13:06:02.065</div>
                    <div style="font-size:30px;margin-top:30px;">Utilizador: miguel</div>
                    <p style="display: flex;justify-content:end;">
                        <button style="font-size:20px;padding:20px;border-radius:30px;;border:1px solid lightblue;background:none;color:lightblue;cursor:pointer;">Criar jogo</button>
                    </p>
                </div>
            </div>
    </div>

    
  </body>
</html>