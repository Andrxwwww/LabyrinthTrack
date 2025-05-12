DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_jogo_JSON`(IN `p_IDJogo` INT, IN `p_JSONData` JSON)
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

IF v_EstadoJogo = 'running' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Apenas pode alterar jogos no estado pending ou finished"; END IF;

UPDATE jogo
SET 

Descricao = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_JSONData,'$.Descricao')),Descricao),
spamTol = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_JSONData,'$.spamTol')),spamTol)
WHERE IDJogo = p_IDJogo;


END$$
DELIMITER ;