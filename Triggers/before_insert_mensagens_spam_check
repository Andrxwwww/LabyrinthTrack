DELIMITER //

CREATE TRIGGER before_insert_mensagens_spam_check
BEFORE INSERT ON mensagens
FOR EACH ROW
BEGIN
    DECLARE ultima_hora_escrita TIMESTAMP;
    DECLARE ultimo_sensor INT;
    DECLARE spam_tol INT;
    DECLARE diferenca_segundos INT;

    SET ultima_hora_escrita = NULL;
    SET ultimo_sensor = NULL;
    SET spam_tol = NULL;

    SELECT HoraEscrita, Sensor INTO ultima_hora_escrita, ultimo_sensor
    FROM mensagens
    WHERE HoraEscrita IS NOT NULL
    ORDER BY HoraEscrita DESC
    LIMIT 1;

    SELECT spamTol INTO spam_tol
    FROM jogo
    WHERE IDJogo = NEW.IdJogo
    LIMIT 1;

    IF spam_tol IS NULL OR spam_tol <= 0 OR ultima_hora_escrita IS NULL THEN
        SET diferenca_segundos = NULL;
    ELSE
        SET diferenca_segundos = TIMESTAMPDIFF(SECOND, ultima_hora_escrita, NEW.HoraEscrita);
    END IF;

    IF diferenca_segundos IS NOT NULL AND diferenca_segundos < spam_tol AND NEW.Sensor = ultimo_sensor THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Inserção descartada: Tempo entre mensagens menor que spamTol e Sensor igual ao último registro.';
    END IF;
END //

DELIMITER ;