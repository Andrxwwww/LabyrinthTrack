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
  
  <body id="dashboard">
  

    <div class="dashboard-container">
            <div class="dashboard-header">
                <div class="dashboard-username"><h1>Utilizador:<?php echo $_SESSION['db_nome']; ?></h1></div>
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
                            <button onclick="location.href='CriarJogo.php';"><i class='bx bx-plus' ></i> Criar novo jogo</button>
                            
                </div>
            </div>
            <table class="table">
            <thead>
                    <tr>
                        <th>Ações</th>
                        <th>ID</th>
                        <th>Descrição</th>
                        <th>Utilizador</th>
                        <th>Data de Inicio</th>
                        <th>Estado</th>
                    </tr>
                </thead>

            <?php foreach ($jogos as $jogo): ?>
                
                <tbody>
                    <tr>
                        <td><div class="action-buttons">
                        <button class="action-button edit" onclick="location.href='editar.php?id=<?php echo $jogo['IDJogo']; ?>';">

                                                <i style="font-size:large;" class='bx bx-edit'></i>
                                            </button>
                                            <button class="action-button delete" onclick="showDeleteGameDialog(<?php echo $jogo['IDJogo']; ?>)">
                                                <i style="font-size:large;color:red;" class='bx bx-trash'></i>
                                            </button>
                                            <button class="action-button start" onclick="startGame(<?php echo $jogo['IDJogo']; ?>)" >
                                                <i style="font-size:large;color:green;" class='bx bx-play'></i>
                                            </button>
                                        </div></td>
                        <td><?php echo $jogo['IDJogo']?></td>
                        <td><?php echo $jogo['Descricao']?></td>
                        <td><?php echo $jogo['jogador']?></td>
                        <td><?php echo $jogo['DataHorainicio']?></td>
                        <td ><div style="margin-left:auto; margin-right:auto;" class="estado-<?php echo $jogo['Estado']; ?>"><?php echo $jogo['Estado']?></div></td>
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
    <script>
function showDeleteGameDialog(idJogo) {
    if (confirm("Tem a certeza que deseja eliminar este jogo?")) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = 'eliminarJogoHandler.php';

        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'id_jogo';
        input.value = idJogo;

        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    }
}
</script>
  </body>
</html>


