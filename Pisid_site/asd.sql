DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `Alterar_utilizador`(IN `p_email` VARCHAR(50), IN `p_json_data` JSON)
BEGIN
    UPDATE utilizador
    SET 
        Nome = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Nome')), Nome),
        Telemovel = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Telemovel')), Telemovel),
        Tipo = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Tipo')), Tipo),
        Grupo = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Grupo')), Grupo),
        Email = COALESCE(JSON_UNQUOTE(JSON_EXTRACT(p_json_data, '$.Email')), Email)
    WHERE Email = p_email;
END$$
DELIMITER ;