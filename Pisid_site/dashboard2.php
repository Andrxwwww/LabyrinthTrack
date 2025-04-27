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
        <?php if($result->num_rows>0) :?> 
            <div class="dashboard-content">
                <div class="dashboard-table">
                    <div class="table-header">
                        <div class="table-title">
                            <h3>Lista de Jogos</h3>
                        </div>
                        <div class="table-button">
                            <button><i class='bx bx-plus' ></i> Criar novo jogo</button>
                            
                </div>
            </div>
            <table class="table">
            <?php foreach ($jogos as $jogo): ?>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Descrição</th>
                        <th>Utilizador</th>
                        <th>Data de Inicio</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><?php echo $jogo['IDJogo']?></td>
                        <td><?php echo $jogo['Descricao']?></td>
                        <td><?php echo $jogo['jogador']?></td>
                        <td><?php echo $jogo['DataHorainicio']?></td>
                    </tr>
                </tbody>
                <?php endforeach; ?>
            </table>
        </div>
    </div>
        <?php else : ?>
            <div class="dashboard-content">
                <div class="dashboard-table">
                    <div class="table-header">
                        <div class="table-title">
                            <h3>Lista de Jogos</h3>
                        </div>
                        <div class="table-button">
                            <button><i class='bx bx-plus' ></i> Criar novo jogo</button>
                            
                </div>
            </div>
            <div >
                                <h3>Não existe nenhum jogo na base de dados</h3>  
                            </div>
        </div>
    </div>
        <?php endif; ?>  
    </div>
  </body>
</html>