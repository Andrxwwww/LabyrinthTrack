DELIMITER //

CREATE TRIGGER after_setupmaze_insert_update
AFTER UPDATE ON SetupMaze
FOR EACH ROW
BEGIN
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
END //

DELIMITER ;