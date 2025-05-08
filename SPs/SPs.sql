DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_jogo`(IN `p_IDJogo` INT, IN `p_descricao` TEXT)
BEGIN
DECLARE v_existsGame BOOLEAN;

    CALL ExistsGame(p_IDJogo, v_existsGame);

    IF v_existsGame = FALSE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Jogo Inserido não existe";
    END IF;

    UPDATE jogo
    SET Descricao = COALESCE(NULLIF(p_descricao, ''), Descricao)
    WHERE IDJogo = p_IDJogo;
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
CREATE DEFINER=`root`@`localhost` PROCEDURE `Criar_jogo`(IN `p_descricao` TEXT)
BEGIN
DECLARE v_exists BOOLEAN DEFAULT FALSE;
    SET @name := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);

    IF CHAR_LENGTH(p_descricao) > 999 THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT= "Descrição demasiado longa";
    END IF;

    INSERT INTO jogo(descricao, jogador, DataHorainicio, estado) 
    VALUES (p_descricao, @name, NOW(), 'pending');
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
CREATE DEFINER=`root`@`localhost` PROCEDURE `EditGameAdmin`(IN `p_IDJogo` INT, IN `p_jogador` VARCHAR(50), IN `p_descricao` TEXT, IN `p_estado` VARCHAR(20), IN `p_score` DOUBLE)
BEGIN
DECLARE v_existsGame BOOLEAN;
DECLARE v_existsJogador BOOLEAN;
DECLARE v_isGameCreator BOOLEAN;

IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";END IF;
IF p_jogador IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogador";END IF;

CALL ExistsGame(p_IDJogo,v_existsGame);
CALL ExistsUtilizador(p_jogador, v_existsJogador);
CALL IsGameCreator(p_IDJogo, p_jogador, v_isGameCreator);


IF v_existsGame = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Jogo Inserido não existe";
END IF;
IF v_existsJogador = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Jogador Inserido não existe";
END IF;
IF v_isGameCreator = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Jogador Inserido não é o criador deste jogo existe";
END IF;
IF p_estado IS NOT NULL AND p_estado NOT IN ('pending','running','finished') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Estado inválido ou Nulo";END IF;
START TRANSACTION;

UPDATE jogo SET Descricao = COALESCE(NULLIF(p_descricao,''),Descricao) ,
Estado =  COALESCE(NULLIF(p_estado,''),Estado),
Score =  COALESCE(p_score,Score) WHERE IDJogo = p_IDJogo;

COMMIT;

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Eliminar_Jogo`(IN `p_IDJogo` INT)
BEGIN

DECLARE v_existsGame BOOLEAN;

IF (p_IDJogo IS NULL) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum ID de Jogo";END IF;


CALL ExistsGame(p_IDJogo,v_existsGame);
 
IF(v_existsGame = FALSE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não existe nenhum jogo com esse ID";END IF;

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
CREATE DEFINER=`root`@`localhost` PROCEDURE `FinishGame`(IN `p_IDJogo` INT)
BEGIN 

DECLARE v_existsGame BOOLEAN DEFAULT FALSE;
DECLARE v_isGameRunning BOOLEAN DEFAULT FALSE;
DECLARE v_isGameFinished BOOLEAN DEFAULT FALSE;

IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";END IF;

CALL ExistsGame(p_IDJogo,v_existsGame);
CALL IsGameRunning(p_IDJogo,v_isGameRunning);
CALL IsGameFinished(p_IDJogo, v_isGameFinished);
IF v_existsGame = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "O jogo inserido não existe";END IF;
IF v_isGameFinished = TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este jogo já foi finalizado";END IF;
IF v_isGameRunning = FALSE THEN SIGNAL SQLSTATE '45000' set MESSAGE_TEXT = "O jogo precisa de estar a correr para poder ser finalizado";END IF;

UPDATE jogo SET Estado = 'finished' WHERE IDJogo= p_IDJogo; 

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `GetGames`(IN `p_grupo` INT)
BEGIN

SELECT * FROM jogo j INNER JOIN utilizador u ON j.jogador = u.Email WHERE u.Grupo = p_grupo;

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `IsGameCreator`(IN `p_IDJogo` INT, IN `p_jogador` VARCHAR(50), OUT `p_creator` BOOLEAN)
BEGIN

DECLARE count INT;

DECLARE v_existsGame BOOLEAN;
DECLARE v_existsJogador BOOLEAN;
IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";
END IF;

IF p_jogador IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum utilizador para fazer a verificação";
END IF;

CALL ExistsGame(p_IDJogo,v_existsGame);
CALL ExistsUtilizador(p_jogador,v_existsJogador);

IF v_existsGame= FALSE THEN 
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi encontrado nenhum jogo com esse ID";
END IF;

IF v_existsJogador= FALSE THEN 
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi encontrado nenhum utilizador com esse Email";
END IF;
SELECT COUNT(*) INTO count FROM jogo WHERE jogo.IDJogo = p_IDJogo AND jogo.jogador = p_jogador;
 
SET p_creator = (count > 0);

END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `IsGameFinished`(IN `p_IDJogo` INT, OUT `p_finished` BOOLEAN)
BEGIN

DECLARE v_existsGame BOOLEAN DEFAULT FALSE;
DECLARE v_count INT;

IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";END IF;

CALL ExistsGame(p_IDJogo,v_existsGame);

IF v_existsGame = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT ="O jogo inserido não existe";END IF;

SELECT COUNT(*) INTO v_count FROM jogo WHERE IDJogo = p_IDJogo AND Estado = 'finished';

SET p_finished = (v_count > 0);
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `IsGameRunning`(IN `p_IDJogo` INT, OUT `p_running` INT)
BEGIN

DECLARE v_existsGame BOOLEAN DEFAULT FALSE;
DECLARE v_count INT;

IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";END IF;

CALL ExistsGame(p_IDJogo,v_existsGame);

IF v_existsGame = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT ="O jogo inserido não existe";END IF;

SELECT COUNT(*) INTO v_count FROM jogo WHERE IDJogo = p_IDJogo AND Estado = 'running';

SET p_running = (v_count > 0);
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Remover_utilizador`(IN `p_utilizador` VARCHAR(50))
BEGIN
DECLARE v_existsUtilizador BOOLEAN;

IF (p_utilizador IS NULL OR p_utilizador = '') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum utilizador";END IF;

CALL ExistsUtilizador(p_utilizador,v_existsUtilizador);

IF (v_existsUtilizador = FALSE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Utilizador não existe";END IF;

DELETE FROM utilizador WHERE  Email= p_utilizador;
END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `StartRunGame`(IN `p_IDJogo` INT, IN `p_jogador` VARCHAR(50))
BEGIN

DECLARE v_alreadyRunningGame BOOLEAN DEFAULT FALSE;
DECLARE v_existsUser BOOLEAN DEFAULT FALSE;
DECLARE v_isGameCreator BOOLEAN DEFAULT FALSE;
DECLARE v_existsGame BOOLEAN DEFAULT FALSE;
DECLARE v_gameRunning BOOLEAN DEFAULT FALSE;
DECLARE v_gameFinished BOOLEAN DEFAULT FALSE;
IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Nenhum jogo foi inserido";END IF;
IF p_jogador IS NULL OR CHAR_LENGTH(TRIM(p_jogador)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Nenhum email de utilizador foi inserido";END IF;

CALL ExistsUtilizador(p_jogador,v_existsUser);
CALL ExistsGame(p_IDJogo,v_existsGame);
CALL IsGameCreator(p_IDJogo,p_jogador,v_IsGameCreator);
CALL IsGameFinished(p_IDJogo,v_gameFinished);
CALL IsGameRunning(p_IDJogo,v_gameRunning);

IF v_existsUser = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Utilizador inserido não existe";END IF;
IF v_existsGame = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Jogo inserido não existe";END IF;
IF v_IsGameCreator = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este utilizador não é o criador do jogo";END IF;
IF v_gameFinished = TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este jogo já foi finalizado";END IF;
IF v_gameRunning = TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este jogo já está a decorrer";END IF;


UPDATE jogo SET Estado = 'running' WHERE IDJogo = p_IDJogo AND jogador = p_jogador;


END$$
DELIMITER ;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `UtilizadorActiveGame`(IN `p_jogador` VARCHAR(50), OUT `p_hasActiveGame` BOOLEAN)
BEGIN

DECLARE v_existsUtilizador BOOLEAN DEFAULT FALSE;
DECLARE v_GamesCount INT DEFAULT 0;
IF p_jogador IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi introduzido nenhum utilizador";END IF;

CALL ExistsUtilizador(p_jogador, v_ExistsUtilizador);

IF v_ExistsUtilizador = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Utilizador inserido não existe";END IF;

SELECT COUNT(*) INTO v_GamesCount FROM jogo WHERE jogador = p_jogador AND Estado = 'running';

SET p_hasActiveGame = (v_GamesCount > 0);
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
