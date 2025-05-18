-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 12-Maio-2025 às 22:03
-- Versão do servidor: 10.4.32-MariaDB
-- versão do PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `pisid_sql`
--

DELIMITER $$
--
-- Procedimentos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_jogo` (IN `p_IDJogo` INT, IN `p_descricao` TEXT)   BEGIN
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

CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_jogo_JSON` (IN `p_IDJogo` INT, IN `p_JSONData` JSON)   BEGIN 

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

IF v_EstadoJogo = 'running' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Apenas pode alterar jogos no estado pending ou finished"; END IF;

UPDATE jogo
SET 

Descricao = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_JSONData,'$.Descricao')),Descricao),
spamTol = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_JSONData,'$.spamTol')),spamTol)
WHERE IDJogo = p_IDJogo;


END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_utilizador` (IN `p_email` VARCHAR(50), IN `p_json_data` JSON)   BEGIN
    UPDATE utilizador
    SET 
        Nome = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Nome')), Nome),
        Telemovel = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Telemovel')), Telemovel),
        Tipo = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Tipo')), Tipo),
        Grupo = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Grupo')), Grupo),
        Email = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Email')), Email)
    WHERE Email = p_email;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `Correr_Jogo` (IN `p_IDJogo` INT)   BEGIN

DECLARE v_CriadorJogo VARCHAR(100);
DECLARE v_Tipo VARCHAR(3);
DECLARE v_ExisteJogo BOOLEAN DEFAULT FALSE;
DECLARE v_EstadoJogo VARCHAR(20);
DECLARE v_User VARCHAR(100);
DECLARE v_ExisteOutroJogoRunning BOOLEAN DEFAULT FALSE;
DECLARE v_grupo INT;
IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Nenhum jogo foi inserido";END IF;

SET v_User := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);
SELECT Tipo into v_Tipo FROM utilizador WHERE Email = v_User;
SELECT Jogador INTO v_CriadorJogo FROM jogo WHERE IDJogo = p_IDJogo;
IF v_User <> v_CriadorJogo AND v_Tipo <> 'ADM' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não tem permissões para alterar este jogo";END IF;


CALL ExistsGame(p_IDJogo, v_ExisteJogo);

IF v_ExisteJogo = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "O jogo inserido não existe";END IF;

SELECT Estado into v_EstadoJogo FROM jogo where IDJogo = p_IDJogo;

IF v_EstadoJogo = 'running' OR v_EstadoJogo =  'finished' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Apenas pode começar jogos no estado pending"; END IF;

SELECT Grupo INTO v_grupo FROM utilizador WHERE Email = v_User;

SELECT COUNT(*) INTO v_ExisteOutroJogoRunning 
FROM jogo j JOIN utilizador u on u.Email = j.jogador
WHERE Estado = 'running' AND IDJogo != p_IDJogo AND u.Grupo = v_grupo;  

IF v_ExisteOutroJogoRunning > 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Já existe outro jogo em estado running no mesmo grupo";
END IF;

UPDATE jogo SET Estado = 'running' WHERE IDJogo = p_IDJogo;

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `CreateDbUser` (IN `p_username` VARCHAR(100), IN `p_password` VARCHAR(100))   BEGIN

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

CREATE DEFINER=`root`@`localhost` PROCEDURE `Criar_jogo` (IN `p_descricao` TEXT, IN `p_spamTol` INT(11))   BEGIN
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

CREATE DEFINER=`root`@`localhost` PROCEDURE `Criar_jogo_JSON` (IN `p_JSONData` JSON)   BEGIN

DECLARE v_User VARCHAR(100);
DECLARE v_Descricao TEXT;
DECLARE v_spamTol INT;

SET v_User := SUBSTRING_INDEX(SESSION_USER(), '@localhost', 1);


SET v_Descricao = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_JSONData,'$.Descricao')),"");
SET v_spamTol = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_JSONData,'$.spamTol')),2);

IF v_User IS NULL OR CHAR_LENGTH(TRIM(v_User)) =0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT="Nenhum utilizador encontrado";END IF;
    IF CHAR_LENGTH(v_descricao) > 999 THEN 
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT= "Descrição demasiado longa";
    END IF;
	
    IF v_spamTol <0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Valor não pode ser nulo ou menor que 0";END IF;
    
    INSERT INTO jogo(descricao, jogador, DataHorainicio, estado,spamTol) 
    VALUES (v_Descricao,v_User, NOW(), 'pending',v_spamTol);

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `Criar_utilizador` (IN `p_Nome` VARCHAR(100), IN `p_Telemovel` VARCHAR(12), IN `p_Tipo` VARCHAR(20), IN `p_Grupo` VARCHAR(20), IN `p_Email` VARCHAR(50), IN `p_Password` VARCHAR(100))   BEGIN

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

CREATE DEFINER=`root`@`localhost` PROCEDURE `Eliminar_Jogo` (IN `p_IDJogo` INT)   BEGIN

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

CREATE DEFINER=`root`@`localhost` PROCEDURE `ExistsGame` (IN `p_IDJogo` INT, OUT `p_exists` BOOLEAN)   BEGIN
DECLARE count INT;

IF p_IDJogo IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum jogo";END IF;
SELECT COUNT(*) INTO count from jogo WHERE jogo.IDJogo = p_IDJogo;

SET p_exists = (count > 0);
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `ExistsUtilizador` (IN `p_Email` VARCHAR(50), OUT `p_exists` BOOLEAN)   BEGIN 
 DECLARE count INT;
 DECLARE v_validEmail BOOLEAN DEFAULT FALSE;
 CALL ValidEmail(p_Email,v_validEmail);
 
 IF p_Email IS NULL OR CHAR_LENGTH(TRIM(p_Email)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum utilizador";END IF;
IF v_validEmail = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Email com formato invalido";END IF;
 SELECT COUNT(*) INTO count FROM utilizador
WHERE utilizador.Email = p_Email;
 SET p_exists = (count > 0);

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `GetGames` (IN `p_grupo` INT)   BEGIN

SELECT * FROM jogo j INNER JOIN utilizador u ON j.jogador = u.Email WHERE u.Grupo = p_grupo;

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `Remover_utilizador` (IN `p_utilizador` VARCHAR(50))   BEGIN
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

CREATE DEFINER=`root`@`localhost` PROCEDURE `ValidEmail` (IN `p_Email` VARCHAR(50), OUT `p_isValid` BOOLEAN)   BEGIN 

IF p_Email REGEXP '^[A-Za-z0-9_.%+-]+@[A-Za-z0-9_%-]+\\.[A-Za-z0-9_-]+$' THEN SET p_isValid =TRUE; ELSE
 SET p_isValid = FALSE;
 END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estrutura da tabela `configs`
--

CREATE TABLE `configs` (
  `chave` varchar(255) NOT NULL,
  `valor` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `configs`
--

INSERT INTO `configs` (`chave`, `valor`) VALUES
('datetime_threshold', '5'),
('limite_80', '0.8'),
('limite_90', '0.9'),
('limite_desvio_padrao', '3'),
('num_sala_max', '10'),
('num_sala_min', '0'),
('qtd_valores_sound_max', '4'),
('qtd_valores_sound_min', '2'),
('status_cansado', '2'),
('status_nenhuma_porta', '0'),
('status_tudoOK', '1');

-- --------------------------------------------------------

--
-- Estrutura da tabela `corridor`
--

CREATE TABLE `corridor` (
  `Rooma` int(11) NOT NULL,
  `Roomb` int(11) NOT NULL,
  `Distance` int(11) NOT NULL,
  `ID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Extraindo dados da tabela `corridor`
--

INSERT INTO `corridor` (`Rooma`, `Roomb`, `Distance`, `ID`) VALUES
(1, 2, 16, 1),
(1, 3, 20, 2),
(2, 4, 20, 3),
(2, 5, 20, 4),
(3, 2, 20, 5),
(4, 5, 20, 6),
(5, 3, 20, 7),
(5, 6, 20, 8),
(5, 7, 20, 9),
(6, 8, 20, 10),
(7, 5, 20, 11),
(8, 9, 20, 12),
(8, 10, 20, 13),
(9, 7, 20, 14),
(10, 1, 20, 15);

-- --------------------------------------------------------

--
-- Estrutura da tabela `jogo`
--

CREATE TABLE `jogo` (
  `IDJogo` int(11) NOT NULL,
  `Descricao` text NOT NULL,
  `jogador` varchar(50) NOT NULL,
  `DataHorainicio` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `Estado` enum('pending','running','finished') NOT NULL DEFAULT 'pending',
  `Score` double NOT NULL DEFAULT -1,
  `spamTol` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `jogo`
--

INSERT INTO `jogo` (`IDJogo`, `Descricao`, `jogador`, `DataHorainicio`, `Estado`, `Score`, `spamTol`) VALUES
(1, '\"Jogo fixe 1\"', 'joao@gmail.com', '2025-05-12 18:05:45', 'finished', 1, 3),
(3, '\"Jogo fixe 2\"', 'joao@gmail.com', '2025-05-10 17:38:43', 'pending', -1, 3),
(6, '\"Jogo fixe 3\"', 'joao@gmail.com', '2025-05-10 17:39:03', 'pending', -1, 3),
(9, '\"Jogo fixe 5\"', 'joao@gmail.com', '2025-05-10 17:39:18', 'pending', -1, 3),
(10, 'testestestes', 'andre@gmail.com', '2025-05-12 19:40:18', 'finished', 9.5, 5);

-- --------------------------------------------------------

--
-- Estrutura da tabela `medicoespassagens`
--

CREATE TABLE `medicoespassagens` (
  `IDMedicao` int(11) NOT NULL,
  `Hora` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `SalaOrigem` int(11) NOT NULL,
  `SalaDestino` int(11) NOT NULL,
  `Marsami` int(11) NOT NULL,
  `Status` int(11) NOT NULL,
  `IDJogo` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Acionadores `medicoespassagens`
--
DELIMITER $$
CREATE TRIGGER `after_medicoespassagens_insert` AFTER INSERT ON `medicoespassagens` FOR EACH ROW BEGIN
    -- Apenas considera inserção na SalaDestino se SalaOrigem = 0
    IF NEW.SalaOrigem = 0 AND NEW.SalaDestino != 0 THEN
        INSERT INTO ocupacaolabirinto (IDJogo, Sala, NumeroMarsamisOdd, NumeroMarsamisEven)
        VALUES (NEW.IDJogo, NEW.SalaDestino,
                IF(NEW.Marsami % 2 = 1, 1, 0),
                IF(NEW.Marsami % 2 = 0, 1, 0)
        )
        ON DUPLICATE KEY UPDATE
            NumeroMarsamisOdd = NumeroMarsamisOdd + IF(NEW.Marsami % 2 = 1, 1, 0),
            NumeroMarsamisEven = NumeroMarsamisEven + IF(NEW.Marsami % 2 = 0, 1, 0);
    END IF;

    -- Atualiza a sala de destino e origem apenas se a SalaOrigem for diferente de 0 e SalaDestino diferente de 0
    IF NEW.SalaOrigem != 0 AND NEW.SalaDestino != 0 THEN
        -- Incrementa na sala destino
        INSERT INTO ocupacaolabirinto (IDJogo, Sala, NumeroMarsamisOdd, NumeroMarsamisEven)
        VALUES (NEW.IDJogo, NEW.SalaDestino,
                IF(NEW.Marsami % 2 = 1, 1, 0),
                IF(NEW.Marsami % 2 = 0, 1, 0)
        )
        ON DUPLICATE KEY UPDATE
            NumeroMarsamisOdd = NumeroMarsamisOdd + IF(NEW.Marsami % 2 = 1, 1, 0),
            NumeroMarsamisEven = NumeroMarsamisEven + IF(NEW.Marsami % 2 = 0, 1, 0);

        -- Decrementa na sala origem
        UPDATE ocupacaolabirinto
        SET NumeroMarsamisOdd = NumeroMarsamisOdd - IF(NEW.Marsami % 2 = 1, 1, 0),
            NumeroMarsamisEven = NumeroMarsamisEven - IF(NEW.Marsami % 2 = 0, 1, 0)
        WHERE IDJogo = NEW.IDJogo AND Sala = NEW.SalaOrigem;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estrutura da tabela `mensagens`
--

CREATE TABLE `mensagens` (
  `ID` int(11) NOT NULL,
  `Hora` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  `Sala` int(11) DEFAULT NULL,
  `Sensor` int(11) NOT NULL,
  `Leitura` decimal(6,2) NOT NULL,
  `TipoAlerta` varchar(55) NOT NULL,
  `Msg` varchar(100) NOT NULL,
  `HoraEscrita` timestamp NULL DEFAULT current_timestamp(),
  `IDJogo` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Acionadores `mensagens`
--
DELIMITER $$
CREATE TRIGGER `before_insert_mensagens_spam_check` BEFORE INSERT ON `mensagens` FOR EACH ROW BEGIN
    DECLARE ultima_hora_escrita TIMESTAMP;
    DECLARE ultimo_sensor INT;
    DECLARE spam_tol INT;
    DECLARE diferenca_segundos INT;

    -- Obter a HoraEscrita e Sensor do último registro inserido em mensagens
    SELECT HoraEscrita, Sensor INTO ultima_hora_escrita, ultimo_sensor
    FROM mensagens
    ORDER BY HoraEscrita DESC
    LIMIT 1;

    -- Obter o valor de spamTol da tabela jogo para o IdJogo do novo registro
    SELECT spamTol INTO spam_tol
    FROM jogo
    WHERE IDJogo = NEW.IdJogo;

    -- Se spamTol for <= 0, ignorar a verificação
    IF spam_tol IS NULL OR spam_tol <= 0 THEN
        SET diferenca_segundos = NULL; -- Permitir inserção
    ELSEIF ultima_hora_escrita IS NULL THEN
        SET diferenca_segundos = NULL; -- Permitir inserção (não há registros anteriores)
    ELSE
        -- Calcular a diferença em segundos entre a nova HoraEscrita e a última HoraEscrita
        SET diferenca_segundos = TIMESTAMPDIFF(SECOND, ultima_hora_escrita, NEW.HoraEscrita);
    END IF;

    -- Se a diferença for menor que spamTol e o Sensor for igual ao último, descartar a inserção
    IF diferenca_segundos IS NOT NULL AND diferenca_segundos < spam_tol AND NEW.Sensor = ultimo_sensor THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Inserção descartada: Tempo entre mensagens menor que spamTol e Sensor igual ao último registro.';
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estrutura da tabela `ocupacaolabirinto`
--

CREATE TABLE `ocupacaolabirinto` (
  `IDJogo` int(11) NOT NULL,
  `NumeroMarsamisOdd` int(11) NOT NULL,
  `NumeroMarsamisEven` int(11) NOT NULL,
  `Sala` int(11) NOT NULL,
  `tentativas` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `setupmaze`
--

CREATE TABLE `setupmaze` (
  `normalnoise` decimal(4,2) NOT NULL,
  `numberrooms` int(11) NOT NULL,
  `numbermarsamis` int(11) NOT NULL,
  `numberplayers` int(11) NOT NULL,
  `noisevartoleration` decimal(5,2) NOT NULL,
  `ID` int(11) NOT NULL,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Extraindo dados da tabela `setupmaze`
--

INSERT INTO `setupmaze` (`normalnoise`, `numberrooms`, `numbermarsamis`, `numberplayers`, `noisevartoleration`, `ID`, `last_updated`) VALUES
(19.00, 10, 30, 40, 2.50, 0, '0000-00-00 00:00:00'),
(19.20, 10, 30, 40, 2.00, 1, '2025-05-12 19:43:54');

--
-- Acionadores `setupmaze`
--
DELIMITER $$
CREATE TRIGGER `after_setupmaze_insert` AFTER INSERT ON `setupmaze` FOR EACH ROW BEGIN
    DECLARE current_idjogo INT;
    DECLARE sala_counter INT DEFAULT 1;

    -- Busca o IDJogo do jogo "running"
    SELECT IDJogo INTO current_idjogo 
    FROM Jogo 
    WHERE Estado = 'running' 
    LIMIT 1;

    IF current_idjogo IS NOT NULL THEN
        -- Remove salas antigas do mesmo jogo (se necessário)
        DELETE FROM ocupacaolabirinto 
        WHERE IDJogo = current_idjogo;

        -- Insere novas salas (1 até numberrooms)
        WHILE sala_counter <= NEW.numberrooms DO
            INSERT INTO ocupacaolabirinto (
                IDJogo, 
                NumeroMarsamisOdd, 
                NumeroMarsamisEven, 
                Sala, 
                Tentativas
            ) VALUES (
                current_idjogo, 
                0, 
                0, 
                sala_counter, 
                0
            );
            SET sala_counter = sala_counter + 1;
        END WHILE;
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `after_setupmaze_update` AFTER UPDATE ON `setupmaze` FOR EACH ROW BEGIN
    DECLARE current_idjogo INT;
    DECLARE sala_counter INT DEFAULT 1;

    -- Busca o IDJogo do jogo "running"
    SELECT IDJogo INTO current_idjogo 
    FROM Jogo 
    WHERE Estado = 'running' 
    LIMIT 1;

    IF current_idjogo IS NOT NULL THEN
        -- Remove salas antigas do mesmo jogo (se necessário)
        DELETE FROM ocupacaolabirinto 
        WHERE IDJogo = current_idjogo;

        -- Insere novas salas (1 até numberrooms)
        WHILE sala_counter <= NEW.numberrooms DO
            INSERT INTO ocupacaolabirinto (
                IDJogo, 
                NumeroMarsamisOdd, 
                NumeroMarsamisEven, 
                Sala, 
                Tentativas
            ) VALUES (
                current_idjogo, 
                0, 
                0, 
                sala_counter, 
                0
            );
            SET sala_counter = sala_counter + 1;
        END WHILE;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estrutura da tabela `sound`
--

CREATE TABLE `sound` (
  `IDSound` int(11) NOT NULL,
  `Hour` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  `Sound` varchar(12) NOT NULL,
  `IdJogo` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `utilizador`
--

CREATE TABLE `utilizador` (
  `Nome` varchar(100) NOT NULL,
  `Telemovel` varchar(12) NOT NULL,
  `Tipo` enum('USER','ADMIN','SCRIPT') NOT NULL,
  `Grupo` int(11) NOT NULL,
  `Email` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `utilizador`
--

INSERT INTO `utilizador` (`Nome`, `Telemovel`, `Tipo`, `Grupo`, `Email`) VALUES
('Andre', '910110110', 'USER', 15, 'andre@gmail.com'),
('Joao', '910110110', 'USER', 15, 'joao@gmail.com');

--
-- Índices para tabelas despejadas
--

--
-- Índices para tabela `configs`
--
ALTER TABLE `configs`
  ADD PRIMARY KEY (`chave`);

--
-- Índices para tabela `corridor`
--
ALTER TABLE `corridor`
  ADD PRIMARY KEY (`ID`);

--
-- Índices para tabela `jogo`
--
ALTER TABLE `jogo`
  ADD PRIMARY KEY (`IDJogo`),
  ADD KEY `jogo_ibfk_1` (`jogador`);

--
-- Índices para tabela `medicoespassagens`
--
ALTER TABLE `medicoespassagens`
  ADD PRIMARY KEY (`IDMedicao`),
  ADD KEY `jo` (`IDJogo`);

--
-- Índices para tabela `mensagens`
--
ALTER TABLE `mensagens`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `chaveestrageira3` (`IDJogo`);

--
-- Índices para tabela `ocupacaolabirinto`
--
ALTER TABLE `ocupacaolabirinto`
  ADD PRIMARY KEY (`IDJogo`,`Sala`),
  ADD KEY `IDJogo` (`IDJogo`);

--
-- Índices para tabela `setupmaze`
--
ALTER TABLE `setupmaze`
  ADD PRIMARY KEY (`ID`);

--
-- Índices para tabela `sound`
--
ALTER TABLE `sound`
  ADD PRIMARY KEY (`IDSound`),
  ADD KEY `chaveestrageira2` (`IdJogo`);

--
-- Índices para tabela `utilizador`
--
ALTER TABLE `utilizador`
  ADD PRIMARY KEY (`Email`);

--
-- AUTO_INCREMENT de tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `corridor`
--
ALTER TABLE `corridor`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de tabela `jogo`
--
ALTER TABLE `jogo`
  MODIFY `IDJogo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de tabela `mensagens`
--
ALTER TABLE `mensagens`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restrições para despejos de tabelas
--

--
-- Limitadores para a tabela `jogo`
--
ALTER TABLE `jogo`
  ADD CONSTRAINT `jogo_ibfk_1` FOREIGN KEY (`jogador`) REFERENCES `utilizador` (`Email`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limitadores para a tabela `medicoespassagens`
--
ALTER TABLE `medicoespassagens`
  ADD CONSTRAINT `jo` FOREIGN KEY (`IDJogo`) REFERENCES `jogo` (`IDJogo`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limitadores para a tabela `mensagens`
--
ALTER TABLE `mensagens`
  ADD CONSTRAINT `chaveestrageira3` FOREIGN KEY (`IDJogo`) REFERENCES `jogo` (`IDJogo`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limitadores para a tabela `ocupacaolabirinto`
--
ALTER TABLE `ocupacaolabirinto`
  ADD CONSTRAINT `jogo_jogo` FOREIGN KEY (`IDJogo`) REFERENCES `jogo` (`IDJogo`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limitadores para a tabela `sound`
--
ALTER TABLE `sound`
  ADD CONSTRAINT `chaveestrageira2` FOREIGN KEY (`IdJogo`) REFERENCES `jogo` (`IDJogo`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
