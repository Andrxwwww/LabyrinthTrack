<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Pisid</title>
    <link
      href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="style.css?v=<?php echo time(); ?>">
  </head>
  <body id="login">
    <div class="flip-card">
      <div class="flip-inner">
        <div class="card-front">
          <form action="login.php" method="post">
            <h1>Login</h1>
            <div class="input-box">
              <input type="email" placeholder="Email de utilizador" name="Email" required />
              <i class="bx bx-envelope"></i>
            </div>
            <div class="input-box">
              <input type="password" placeholder="Password" name="Password" required />
              <i class="bx bxs-lock-alt"></i>
            </div>
            <button type="submit" class="btn">
              <span>Login</span>
            </button>
            <div class="register-link">
              <p><a href="#" id="show-register">  </a></p>
            </div>
          </form>
        </div>

        <div class="card-back">
          <form action="register.php" method="post">
            <h1>Registar</h1>
            <div class="input-box">
              <input type="text" placeholder="Nome" name="Nome" required />
              <i class="bx bxs-user"></i>
            </div>
            <div class="input-box">
              <input type="email" placeholder="Email" name="Email" required />
              <i class="bx bx-user"></i>
            </div>
            <div class="input-box">
              <input type="number" placeholder="Telemóvel" Name="Telemovel" required />
              <i class="bx bxs-phone"></i>
            </div>
            <div class="input-box">
              <input type="text" placeholder="Tipo" name="Tipo" required />
              <i class="bx bx-user"></i>
            </div>
            <div class="input-box">
              <input type="number" placeholder="Grupo" name="Grupo" required />
              <i class="bx bx-user"></i>
            </div>
            <div class="input-box">
              <input type="password" placeholder="Password" name="Password" required />
              <i class="bx bxs-lock-alt"></i>
            </div>
            <button type="submit" class="btn">
              <span>Registar</span>
            </button>
            <div class="register-link">
              <p><a href="#" id="show-login">Já tenho Conta</a></p>
            </div>
          </form>
        </div>
      </div>
    </div>
    <script src="script.js"></script>
  </body>
</html>

<?php if (isset($_GET['error'])): ?>
<div class="popup-error">
    <?php echo "Password ou Email incorretos" ?>
</div>
<?php endif; ?>