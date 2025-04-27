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
                <div class="dashboard-username"><h1>Utilizador:<?php echo $_SESSION['name']; ?></h1></div>
            <div class="dashboard-search">
                <input placeholder="Pesquisar jogo"/>
            </div>
            <div class="dashboard-logout">
                <button><i class='bx bxs-door-open'></i></button>
            </div>
        </div>
            <div class="dashboard-content">
                <div class="dashboard-table" style="min-height:0; padding:0;">
            <table class="table">
            
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Descrição</th>
                        <th>Jogador</th>
                        <th>Data de Inicio</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td>Jogo de Teste</td>
                        <td>Miguel</td>
                        <td>2025-03-20 13:06:02.065 </td>
                        <td >Finalizado</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div style="width: 90%;background-color:white;margin:20px auto;padding:40px 0;border-radius:20px;">
        <div style="display:flex; justify-content:center;align-items:center;flex-direction:column;">
            <label style="margin-bottom:30px;font-weight:600;font-size:20px;">Editar descrição</label>
            <textarea name="descricao" id="descricao" cols="240" rows="10" placeholder="Jogo de Teste"></textarea>
        </div>
        <div style="margin-top:40px;display:flex; justify-content:end;align-items:center;padding-right:30px;font-size:15px;">
            <button style="margin-right:20px;padding:10px;border-radius:10px;border:none;font-size:15px;background-color:lightgreen;color:white;font-weight:700">Guardar Alterações</button>
            <button style="margin-right:20px;padding:10px;border-radius:10px;border:none;font-size:15px;background-color:red;color:white;font-weight:700">Eliminar jogo</button>
            <button style="padding:10px;border-radius:10px;border:none;color:white;font-size:15px;background-color:gray;font-weight:700;">Voltar</button>

        </div>
    </div>
    </div>

    
  </body>
</html>