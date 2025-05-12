<?php
session_start();

$username = $_SESSION['db_email'];
$password = $_SESSION['db_pass'];
$grupo = $_SESSION['db_grupo'];
$dbname = "pisid_sql";

$connPisid = new mysqli('localhost', $username, $password, $dbname);
if ($connPisid->connect_error) {
    die("Ligação falhou: " . $connPisid->connect_error);
}


$sql = "call GetGames($grupo)";
$result = mysqli_query($connPisid, $sql);
$jogos = $result->fetch_all(MYSQLI_ASSOC);
mysqli_close ($connPisid);
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
  <form action="criarJogoHandler.php" method="post">
    <div class="dashboard-container" style="height:20vh">
            <div class="dashboard-header">
                <div class="dashboard-username"><h1>Utilizador: <?php echo $_SESSION['db_nome']; ?></h1></div>
            <div class="dashboard-search">
                <input placeholder="Pesquisar jogo"/>
            </div>
            <div class="dashboard-logout">
    <a href="logout.php" title="Terminar sessão" style="text-decoration: none; color: inherit;">
        <button type="button" style="background: none; border: none; cursor: pointer;">
            <i class='bx bxs-door-open' style="font-size: 24px;"></i>
        </button>
    </a>
</div>
        </div>
            <div class="" style="background-color:white;margin:40px 70px;padding:30px;border-radius:30px;">
                <div><h1>Criar um jogo novo:</h1></div>
                <div style="margin-top:60px;">
                    <div style="display: flex;justify-content:start;align-items:center;margin-top:30px;">
                        <label style="font-size:30px;margin-right:10px;">Descrição:</label>
                        <textarea name="descricao" id="descricao" cols="150" rows="4" placeholder=""></textarea>
                    </div>
                    <div style="display: flex;justify-content:start;align-items:center;margin-top:30px;">
                        <label style="font-size:30px;margin-right:10px;">Delay Time entre mensagens:</label>
                        <input name="spamTol" id="spamTol" style="width:5%;height:50px;margin-right:20px"  /> segundos
                    </div>
                    <div style="font-size:30px;margin-top:30px;">Utilizador: <?php echo $_SESSION['db_nome']; ?></div>
                    <p style="display: flex;justify-content:end;">
                        <button style="font-size:20px;padding:20px;border-radius:30px;;border:1px solid lightblue;background:none;color:lightblue;cursor:pointer;">Criar jogo</button>
                    </p>
                </div>
            </div>
    </div>
</form>
    
  </body>
</html>