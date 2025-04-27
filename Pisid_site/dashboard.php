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
  <body id="dashboard">
    <div class="dashboard-container">
            <div class="dashboard-header">
                <div class="dashboard-username"><h1>Utilizador:<?php echo $_SESSION['name']; ?></h1></div>
            <div class="dashboard-search">
                <input placeholder="Pesquisar jogo"/>
            </div>
            <div class="dashboard-logout">
                <button><i class='bx bxs-door-open'></i></button>
            </div>
        </div>
            <div class="dashboard-content">
                <div class="dashboard-table">
                    <div class="table-header">
                        <div class="table-title">
                            <h3>Lista de Jogos</h3>
                        </div>
                        <div class="table-button">
                            <button href="/CriarJogo.php" ><i class='bx bx-plus'></i> Criar novo jogo</button>
                            
                </div>
            </div>
            <table class="table">
            
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Descrição</th>
                        <th>Jogador</th>
                        <th>Data de Inicio</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td>Jogo de Teste</td>
                        <td>Miguel</td>
                        <td>2025-03-20 13:06:02.065 </td>
                        <td style="display: flex;justify-content:start;align-items:center;padding-top:10px;"><i class='bx bxs-edit-alt' style="font-size:30px" class="edit-icon"></i></td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td>Jogo de Teste 2</td>
                        <td>Ricardo</td>
                        <td>2025-03-20 14:06:02.065</td>
                        <td style="display: flex;justify-content:start;align-items:center;padding-top:10px;"><i class='bx bxs-edit-alt' style="font-size:30px" class="edit-icon"></i></td>
                    </tr>
                </tbody>
           
            </table>
        </div>
    </div>
        
    </div>
  </body>
</html>