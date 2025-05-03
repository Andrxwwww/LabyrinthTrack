import mariadb
import sys

# Configurações iniciais para evitar variáveis não definidas
db = None
cursor = None
db_prof = None
cursor_prof = None

try:
    # Conexão com o banco de dados local
    db = mariadb.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="pisid_sql"
    )
    cursor = db.cursor()
    print("[SUCESSO] Conectado ao banco de dados local.")


except mariadb.Error as e:
    print(f"[ERRO] Falha na conexão com o banco local: {e}")
    sys.exit(1)  # Encerra o programa se a conexão crítica falhar

try:
    # Conexão com o banco do professor
    db_prof = mariadb.connect(
        host="194.210.86.10",
        user="aluno",
        password="aluno",
        database="maze"
    )
    cursor_prof = db_prof.cursor()
    print("[SUCESSO] Conectado ao banco do professor.")

except mariadb.Error as e:
    print(f"[ERRO] Falha na conexão com o banco do professor: {e}")
    sys.exit(1)  # Encerra se a conexão com o banco remoto for essencial

# ---------------------------------------------------------------------
# Configuração do MQTT (não requer try...catch, são variáveis estáticas)
# ---------------------------------------------------------------------
MQTT_BROKER ="98.66.160.46"
MQTT_PORT = 1883
GROUP_MQTT_SOUND_TOPIC = "sound_grupo15"
GROUP_MQTT_MOVE_TOPIC = "move_grupo15"
GROUP_MQTT_ACK_TOPIC = "ack_grupo15"
GROUP_MQTT_FAILED_TOPIC = "failed_grupo15"