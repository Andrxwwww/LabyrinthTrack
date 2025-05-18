DELIMITER //

CREATE TRIGGER after_medicoespassagens_insert
AFTER INSERT ON medicoespassagens
FOR EACH ROW
BEGIN
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
END //

DELIMITER ;