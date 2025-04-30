-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 30-Abr-2025 às 23:56
-- Versão do servidor: 10.4.28-MariaDB
-- versão do PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `pisid`
--

DELIMITER $$
--
-- Procedimentos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `CreateUtilizador` (IN `p_Nome` VARCHAR(100), IN `p_Telemovel` VARCHAR(12), IN `p_Tipo` VARCHAR(20), IN `p_Grupo` VARCHAR(20), IN `p_Email` VARCHAR(50), IN `p_Password` VARCHAR(100))   BEGIN

DECLARE v_alreadyExists BOOLEAN DEFAULT FALSE;
DECLARE v_validEmail BOOLEAN DEFAULT FALSE;

IF p_Email IS NULL OR CHAR_LENGTH(TRIM(p_Email)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum Email";END IF;

IF p_Password IS NULL OR CHAR_LENGTH(TRIM(p_Password)) = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserida nenhuma Password";END IF;

CALL ValidEmail(p_Email,v_validEmail);
                                     
IF v_validEmail = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Email com formato Invalido";END IF;
                                     
CALL ExistsUtilizador(p_Email, v_alreadyExists);
                                     
IF v_alreadyExists = TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este utilizador já existe";END IF;
                                      
                                     
INSERT INTO utilizador (nome, telemovel, tipo, grupo, email)
VALUES (p_nome, p_telemovel, p_tipo, p_grupo, p_email);                                     
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `EditGameAdmin` (IN `p_IDJogo` INT, IN `p_jogador` VARCHAR(50), IN `p_descricao` TEXT, IN `p_estado` VARCHAR(20), IN `p_score` DOUBLE)   BEGIN
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

START TRANSACTION;

UPDATE jogo SET Descricao = COALESCE(NULLIF(p_descricao,''),Descricao) ,
Estado =  COALESCE(NULLIF(p_estado,''),Estado),
Score =  COALESCE(p_score,Score) WHERE IDJogo = p_IDJogo;

COMMIT;

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `EditGameUtilizador` (IN `p_IDJogo` INT, IN `p_jogador` VARCHAR(50), IN `p_descricao` TEXT)   BEGIN
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
UPDATE jogo SET Descricao = COALESCE(NULLIF(p_descricao,''),Descricao) WHERE IDJogo = p_IDJogo;

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `EliminateGame` (IN `p_IDJogo` INT)   BEGIN

DECLARE v_existsGame BOOLEAN;

IF (p_IDJogo IS NULL) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum ID de Jogo";END IF;


CALL ExistsGame(p_IDJogo,v_existsGame);
 
IF(v_existsGame = FALSE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não existe nenhum jogo com esse ID";END IF;

DELETE FROM jogo WHERE IDJogo=p_IDJogo;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `EliminateUtilizador` (IN `p_utilizador` VARCHAR(50))   BEGIN
DECLARE v_existsUtilizador BOOLEAN;

IF (p_utilizador IS NULL OR p_utilizador = '') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi inserido nenhum utilizador";END IF;

CALL ExistsUtilizador(p_utilizador,v_existsUtilizador);

IF (v_existsUtilizador = FALSE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Utilizador não existe";END IF;

DELETE FROM utilizador WHERE  Email= p_utilizador;
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

CREATE DEFINER=`root`@`localhost` PROCEDURE `IsGameCreator` (IN `p_IDJogo` INT, IN `p_jogador` VARCHAR(50), OUT `p_creator` BOOLEAN)   BEGIN

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

CREATE DEFINER=`root`@`localhost` PROCEDURE `StartGame` (IN `p_descricao` TEXT, IN `p_jogador` VARCHAR(50))   BEGIN
DECLARE v_exists BOOLEAN DEFAULT FALSE;
 IF p_jogador IS NULL THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Insira um email válido  e existente para poder criar o jogo";
 END IF;
 

CALL ExistsUtilizador(p_jogador,v_exists);

IF v_exists = FALSE THEN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Este Email não existe na base de dados";
END IF;

IF CHAR_LENGTH(p_descricao) > 999 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT= "Descrição demasiado longa";END IF;
 INSERT INTO jogo(descricao,jogador,DataHorainicio,estado,score) VALUES (p_descricao,p_jogador,NOW(),'Inicial',0);
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `UtilizadorActiveGame` (IN `p_jogador` VARCHAR(50), OUT `p_hasActiveGame` BOOLEAN)   BEGIN

DECLARE v_existsUtilizador BOOLEAN DEFAULT FALSE;
DECLARE v_GamesCount INT DEFAULT 0;
IF p_jogador IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Não foi introduzido nenhum utilizador";END IF;

CALL ExistsUtilizador(p_jogador, v_ExistsUtilizador);

IF v_ExistsUtilizador = FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Utilizador inserido não existe";END IF;

SELECT COUNT(*) INTO v_GamesCount FROM jogo WHERE jogador = p_jogador AND Estado = 'Inicial';

SET p_hasActiveGame = (v_GamesCount > 0);
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
('limite_60', '0.6'),
('limite_80', '0.8'),
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
  `Score` double NOT NULL DEFAULT -1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `jogo`
--

INSERT INTO `jogo` (`IDJogo`, `Descricao`, `jogador`, `DataHorainicio`, `Estado`, `Score`) VALUES
(1, 'Testes', '22', '2025-04-30 16:51:25', 'pending', -1);

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

-- --------------------------------------------------------

--
-- Estrutura da tabela `mensagens`
--

CREATE TABLE `mensagens` (
  `ID` int(11) NOT NULL,
  `Hora` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  `Sala` int(11) NOT NULL,
  `Sensor` int(11) NOT NULL,
  `Leitura` decimal(6,2) NOT NULL,
  `TipoAlerta` int(11) NOT NULL,
  `Msg` varchar(100) NOT NULL,
  `HoraEscrita` timestamp NULL DEFAULT current_timestamp(),
  `IDJogo` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `ocupacaolabirinto`
--

CREATE TABLE `ocupacaolabirinto` (
  `IDJogo` int(11) NOT NULL,
  `NumeroMarsamisOdd` int(11) NOT NULL,
  `NumeroMarsamisEven` int(11) NOT NULL,
  `Sala` int(11) NOT NULL,
  `Tentativas` int(11) NOT NULL DEFAULT 0
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
  `ID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Extraindo dados da tabela `setupmaze`
--

INSERT INTO `setupmaze` (`normalnoise`, `numberrooms`, `numbermarsamis`, `numberplayers`, `noisevartoleration`, `ID`) VALUES
(19.00, 10, 30, 40, 2.50, 0);

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
-- Estrutura da tabela `tipoalerta`
--

CREATE TABLE `tipoalerta` (
  `IDTipoAlerta` int(11) NOT NULL,
  `TipoAlerta` varchar(50) NOT NULL,
  `gravidade` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `tipoalerta`
--

INSERT INTO `tipoalerta` (`IDTipoAlerta`, `TipoAlerta`, `gravidade`) VALUES
(1, 'Warring', 'High');

-- --------------------------------------------------------

--
-- Estrutura da tabela `utilizador`
--

CREATE TABLE `utilizador` (
  `Nome` varchar(100) NOT NULL,
  `Telemovel` varchar(12) NOT NULL,
  `Tipo` varchar(3) NOT NULL,
  `Grupo` int(11) NOT NULL,
  `Email` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `utilizador`
--

INSERT INTO `utilizador` (`Nome`, `Telemovel`, `Tipo`, `Grupo`, `Email`) VALUES
('ff', '22', '22', 22, '22');

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
  ADD KEY `chaveestrageira3` (`IDJogo`),
  ADD KEY `idtipoalerta` (`TipoAlerta`);

--
-- Índices para tabela `ocupacaolabirinto`
--
ALTER TABLE `ocupacaolabirinto`
  ADD PRIMARY KEY (`IDJogo`),
  ADD UNIQUE KEY `Sala` (`Sala`),
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
-- Índices para tabela `tipoalerta`
--
ALTER TABLE `tipoalerta`
  ADD PRIMARY KEY (`IDTipoAlerta`);

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
  MODIFY `IDJogo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `mensagens`
--
ALTER TABLE `mensagens`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

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
  ADD CONSTRAINT `chaveestrageira3` FOREIGN KEY (`IDJogo`) REFERENCES `jogo` (`IDJogo`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `idtipoalerta` FOREIGN KEY (`TipoAlerta`) REFERENCES `tipoalerta` (`IDTipoAlerta`) ON UPDATE CASCADE;

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
