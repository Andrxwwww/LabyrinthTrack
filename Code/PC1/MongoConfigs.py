import sys
from pymongo import MongoClient

# --- Configurações MQTT ---
MQTT_BROKER = "20.39.241.21"
MQTT_PORT = 1883

# -- Configurações de MQTT já pré feitas ---
MQTT_MOVE_TOPIC = "pisid_mazemov_15"  # Tópico para obter a info do movimento
MQTT_SOUND_TOPIC = "pisid_mazesound_15"  # Tópico para obter a info do som

# --- Configurações de MQTT feitas pelo Grupo ---
GROUP_MQTT_MOVE_TOPIC = "move_grupo15"
GROUP_MQTT_SOUND_TOPIC = "sound_grupo15"
GROUP_MQTT_ACK_TOPIC = "ack_grupo15"
GROUP_MQTT_FAILED_TOPIC = "failed_grupo15"
GROUP_MQTT_Alive_TOPIC="keep_alive"

# --- Configurações MongoDB ---
MONGO_URI = "mongodb://localhost:27019/"
MONGO_DB = "PISID_Maze"
MONGO_COLLECTION_MOVE = "Move"
MONGO_COLLECTION_SOUND = "Sound"
MONGO_COLLECTION_FAILED = "Failed"
MONGO_COLLECTION_LASTIDS = "LastIDs"

# --- Conexão Mongo ---
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)  # timeout de 3 segundos
    mongo_client.admin.command('ping')  # força a conexão ao servidor
    db = mongo_client[MONGO_DB]
except Exception as e:
    print(f"[ERRO] Falha na conexão com o MongoDB , por favor tente novamente: {e}")
    sys.exit(1)


# --- Coleções Mongo ---
collection_move = db[MONGO_COLLECTION_MOVE]
collection_sound = db[MONGO_COLLECTION_SOUND]
collection_failed = db[MONGO_COLLECTION_FAILED]
collection_lastids = db[MONGO_COLLECTION_LASTIDS]