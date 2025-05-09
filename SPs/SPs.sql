DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_jogo`(IN `p_IDJogo` INT, IN `p_descricao` TEXT)
BEGIN
DECLARE v_existsGame BOOLEAN;
DECLARE v_Tipo VARCHAR(3);
DECLARE v_CriadorJogo VARCHAR(100);
DECLARE v_EstadoJogo VARCHAR(20);
DECLARE v_User VARCHAR(100);
SET v_User := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);
SELECT Tipo INTO v_Tipo FROM utilizador WHERE Email = v_User;
SELECT Jogador INTO v_CriadorJogo FROM jogo WHERE IDJogo = p_IDJogo;

    CALL ExistsGame(p_IDJogo, v_existsGame);

    IF v_existsGame = FALSE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Jogo Inserido não existe";
    END IF;
	
    IF v_CriadorJogo <> v_User AND v_Tipo <> 'ADM' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "O jogador não tem permissoões para alterar este jogo";END IF;
    
    SELECT Estado into v_EstadoJogo FROM jogo where IDJogo = p_IDJogo;

IF v_EstadoJogo = 'running' OR v_EstadoJogo =  'finished' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Apenas pode começar jogos no estado pending"; END IF;
    
    
    UPDATE jogo
    SET Descricao = COALESCE(NULLIF(p_descricao, ''), Descricao)
    WHERE IDJogo = p_IDJogo;
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Correr_Jogo`(IN `p_IDJogo` INT)
BEGIN

DECLARE v_CriadorJogo VARCHAR(100);
DECLARE v_Tipo VARCHAR(3);
DECLARE v_ExisteJogo BOOLEAN DEFAULT FALSE;
DECLARE v_EstadoJogo VARCHAR(20);
DECLARE v_User VARCHAR(100);
IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Nenhum jogo foi inserido";END IF;

SET v_User := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);
SELECT Tipo into v_Tipo FROM utilizador WHERE Email = v_User;
SELECT Jogador INTO v_CriadorJogo FROM jogo WHERE IDJogo = p_IDJogo;
IF v_User <> v_CriadorJogo AND v_Tipo <> 'ADM' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não tem permissões para alterar este jogo";END IF;


CALL ExistsGame(p_IDJogo, v_ExisteJogo);

IF v_ExisteJogo = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "O jogo inserido não existe";END IF;

SELECT Estado into v_EstadoJogo FROM jogo where IDJogo = p_IDJogo;

IF v_EstadoJogo = 'running' OR v_EstadoJogo =  'finished' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Apenas pode começar jogos no estado pending"; END IF;

UPDATE jogo SET Estado = 'running' WHERE IDJogo = p_IDJogo;

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `CreateDbUser`(IN `p_username` VARCHAR(100), IN `p_password` VARCHAR(100))
BEGIN

  IF p_username IS NULL OR CHAR_LENGTH(TRIM(p_username)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum username";
  END IF;

  IF p_password IS NULL OR CHAR_LENGTH(TRIM(p_password)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserida nenhuma password";
  END IF;

  SET @sql := CONCAT('CREATE USER \'', p_username, '\'@\'localhost\' IDENTIFIED BY \'', p_password, '\'');
  PREPARE stmt FROM @sql;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;

  SET @grant_sql := CONCAT('GRANT ALL PRIVILEGES ON pisid_sql.* TO \'', p_username, '\'@\'localhost\'');
  PREPARE grant_stmt FROM @grant_sql;
  EXECUTE grant_stmt;
  DEALLOCATE PREPARE grant_stmt;

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Criar_jogo`(IN `p_descricao` TEXT, IN `p_spamTol` INT(11))
BEGIN
DECLARE v_exists BOOLEAN DEFAULT FALSE;
DECLARE v_User VARCHAR(100);
    SET v_User := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);


	IF v_User IS NULL OR CHAR_LENGTH(TRIM(v_User)) =0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT="Nenhum utilizador encontrado";END IF;
    IF CHAR_LENGTH(p_descricao) > 999 THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT= "Descrição demasiado longa";
    END IF;
	
    IF p_spamTol IS NULL OR p_spamTol <0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Valor não pode ser nulo ou menor que 0";END IF;
    
    INSERT INTO jogo(descricao, jogador, DataHorainicio, estado,spamTol) 
    VALUES (p_descricao,v_User, NOW(), 'pending',p_spamTol);
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Criar_utilizador`(IN `p_Nome` VARCHAR(100), IN `p_Telemovel` VARCHAR(12), IN `p_Tipo` VARCHAR(20), IN `p_Grupo` VARCHAR(20), IN `p_Email` VARCHAR(50), IN `p_Password` VARCHAR(100))
BEGIN

DECLARE v_alreadyExists BOOLEAN DEFAULT FALSE;
DECLARE v_validEmail BOOLEAN DEFAULT FALSE;

IF p_Email IS NULL OR CHAR_LENGTH(TRIM(p_Email)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum Email";END IF;

IF p_Password IS NULL OR CHAR_LENGTH(TRIM(p_Password)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserida nenhuma Password";END IF;

CALL ValidEmail(p_Email,v_validEmail);
                                     
IF v_validEmail = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Email com formato Invalido";END IF;
                                     
CALL ExistsUtilizador(p_Email, v_alreadyExists);
                                     
IF v_alreadyExists = TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este utilizador já existe";END IF;
                                      
CALL CreateDbUser(p_Email,p_Password);                                     
INSERT INTO utilizador (nome, telemovel, tipo, grupo, email)
VALUES (p_Nome, p_Telemovel, p_Tipo, p_Grupo, p_Email);                                     
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Eliminar_Jogo`(IN `p_IDJogo` INT)
BEGIN

DECLARE v_existsGame BOOLEAN;
DECLARE v_EstadoJogo VARCHAR(20);
DECLARE v_CriadorJogo VARCHAR(100);
DECLARE v_Tipo VARCHAR(3);
DECLARE v_User VARCHAR(100);
SET v_User := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);
SELECT Tipo INTO v_Tipo FROM utilizador WHERE Email = v_User;
SELECT Jogador INTO v_CriadorJogo FROM jogo WHERE IDJogo = p_IDJogo;
IF (p_IDJogo IS NULL) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum ID de Jogo";END IF;


CALL ExistsGame(p_IDJogo,v_existsGame);
 
IF(v_existsGame = FALSE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não existe nenhum jogo com esse ID";END IF;

IF v_CriadorJogo <> v_User AND v_Tipo <> 'ADM' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "O jogador não tem permissoões para alterar este jogo";END IF;
    
    SELECT Estado into v_EstadoJogo FROM jogo where IDJogo = p_IDJogo;

IF v_EstadoJogo = 'running' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não pode eliminar jogos que estão a decorrer"; END IF;

DELETE FROM jogo WHERE IDJogo=p_IDJogo;
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `ExistsGame`(IN `p_IDJogo` INT, OUT `p_exists` BOOLEAN)
BEGIN
DECLARE count INT;

IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";END IF;
SELECT COUNT(*) INTO count from jogo WHERE jogo.IDJogo = p_IDJogo;

SET p_exists = (count > 0);
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `ExistsUtilizador`(IN `p_Email` VARCHAR(50), OUT `p_exists` BOOLEAN)
BEGIN 
 DECLARE count INT;
 DECLARE v_validEmail BOOLEAN DEFAULT FALSE;
 CALL ValidEmail(p_Email,v_validEmail);
 
 IF p_Email IS NULL OR CHAR_LENGTH(TRIM(p_Email)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum utilizador";END IF;
IF v_validEmail = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Email com formato invalido";END IF;
 SELECT COUNT(*) INTO count FROM utilizador
WHERE utilizador.Email = p_Email;
 SET p_exists = (count > 0);

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `GetGames`(IN `p_grupo` INT)
BEGIN

SELECT * FROM jogo j INNER JOIN utilizador u ON j.jogador = u.Email WHERE u.Grupo = p_grupo;

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Remover_utilizador`(IN `p_utilizador` VARCHAR(50))
BEGIN
DECLARE v_existsUtilizador BOOLEAN;

IF (p_utilizador IS NULL OR p_utilizador = '') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum utilizador";END IF;

CALL ExistsUtilizador(p_utilizador,v_existsUtilizador);

IF (v_existsUtilizador = FALSE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Utilizador não existe";END IF;

DELETE FROM utilizador WHERE  Email=p_utilizador;
SET @drop_sql := CONCAT('DROP USER \'', p_utilizador, '\'@\'localhost\'');
PREPARE stmt FROM @drop_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `ValidEmail`(IN `p_Email` VARCHAR(50), OUT `p_isValid` BOOLEAN)
BEGIN 

IF p_Email REGEXP '^[A-Za-z0-9_.%+-]+@[A-Za-z0-9_%-]+\\.[A-Za-z0-9_-]+$' THEN SET p_isValid =TRUE; ELSE
 SET p_isValid = FALSE;
 END IF;
END$$
DELIMITER ;
