<?php
session_start();
include 'db.php';

if (!isset($_GET['id'])) {
    die("ID do jogo não especificado.");
}
$idJogo = intval($_GET['id']);

$sql = "SELECT * FROM jogo WHERE IDJogo = ?";
$stmt = $connPisid->prepare($sql);
$stmt->bind_param("i", $idJogo);
$stmt->execute();
$result = $stmt->get_result();
$jogo = $result->fetch_assoc();
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
    <div class="dashboard-container" style="height:100vh">
            <div class="dashboard-header">
                <div class="dashboard-username"><h1>Utilizador:<?php echo $_SESSION['db_nome']; ?></h1></div>
            <div class="dashboard-search">
                <input placeholder="Pesquisar jogo"/>
            </div>
            <div class="dashboard-logout">
                <button><i class='bx bxs-door-open'></i></button>
            </div>
        </div>
        <div class="form-container">
            <form  class="form" action="editarJogoHandler.php" method="post"> 
                
                    <div  class="form-title">
                        <div>
                            <div class="form-gameid">Detalhe do Jogo #<?php echo htmlspecialchars($jogo['IDJogo']); ?></div>
                            <div class="form-viewinfo">Visualize e edite as informações do jogo</div>
                        </div>
                        <div class="form-estado">
                            <div class="estado-<?php echo htmlspecialchars($jogo['Estado']); ?>"><?php echo htmlspecialchars($jogo['Estado']); ?></div>
                        </div>
                    </div>
                    <div class="form-info">
                        <div class="form-infos">Informações</div>
                        <div>
                            <div class="form-label">Jogador</div>
                            <div class="form-values"><?php echo htmlspecialchars($jogo['jogador']); ?></div>
                        </div>
                        <div>
                            <div class="form-label">Data de Inicio</div>
                            <div class="form-values"><?php echo htmlspecialchars($jogo['DataHorainicio']); ?></div>
                        </div>
                        <div>
                            <div class="form-label"> Descrição</div>
                            <input type="textarea" class="form-description" name="descricao" value=<?php echo htmlspecialchars($jogo['Descricao']); ?> />
                            <input type="hidden" name="id_jogo" value=<?php echo htmlspecialchars($jogo['IDJogo']); ?> />
                        </div>
                    </div>
                    <div class="form-buttons">
                    <div class="form-voltar">
        <button type="button" onclick="location.href='dashboard.php'">Voltar</button></div>
        <div class="form-guardar">
                    <button type="submit" name="id_jogo" value="<?php echo $jogo['IDJogo']; ?>">Guardar Alterações</button>
                </div>
                    </div>
             
            </form>
            </div>
    </div>
  </body>
</html>