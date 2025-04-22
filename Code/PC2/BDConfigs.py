import mariadb

# Configuração do MySQL
db = mariadb.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="pisid_sql"
)

cursor = db.cursor()

# Configuração do MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
GROUP_MQTT_SOUND_TOPIC = "sound_grupo15"
GROUP_MQTT_MOVE_TOPIC = "move_grupo15"
GROUP_MQTT_ACK_TOPIC = "ack_grupo15"
GROUP_MQTT_FAILED_TOPIC = "failed_grupo15"