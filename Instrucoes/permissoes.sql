-- Script to grant permissions to the user "script2" for the pisid_sql schema
GRANT SELECT, INSERT, UPDATE ON pisid_sql.corridor TO "script2";

GRANT SELECT, INSERT, UPDATE ON pisid_sql.setupmaze TO "script2";

GRANT SELECT, UPDATE ON pisid_sql.jogo TO "script2";

GRANT INSERT ON pisid_sql.sound TO "script2";

GRANT INSERT ON pisid_sql.medicoespassagens TO "script2";

GRANT INSERT, SELECT ON pisid_sql.mensagens TO "script2";

GRANT INSERT ON pisid_sql.ocupacaolabirinto TO "script2";
