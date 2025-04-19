import threading
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import time
from datetime import datetime

# Configurações MQTT
# mqtt-dashboard.com broker.hivemq.com broker.emqx.io
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_MOVE_TOPIC = "pisid_mazemov_15"  # Tópico para obter a info do movimento
MQTT_SOUND_TOPIC = "pisid_mazesound_15"  # Tópico para obter a info do som

# Configurações MongoDB
MONGO_URI = "mongodb://localhost:27017/"  # Ajustar conforme necessário
MONGO_DB = "PISID_Maze"
MONGO_COLLECTION_MOVE = "Move"
MONGO_COLLECTION_SOUND = "Sound"
MONGO_COLLECTION_FAILED = "Failed"  # Coleção para guardar os dados que falharam a inserção
MONGO_COLLECTION_LASTIDS = "LastIDs"  # Coleção para guardar os últimos IDs

# Conectar ao MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
collection_move = db[MONGO_COLLECTION_MOVE]
collection_sound = db[MONGO_COLLECTION_SOUND]
collection_failed = db[MONGO_COLLECTION_FAILED]  # Coleção para guardar os dados que falharam a inserção
collection_lastids = db[MONGO_COLLECTION_LASTIDS]  # Coleção para guardar os últimos IDs

# Limpar todas as coleções **REMOVER DEPOIS**
collection_move.delete_many({})
collection_sound.delete_many({})
collection_failed.delete_many({})

# Contador de mensagens recebidas
message_received = 0
lock = threading.Lock()  # Lock para garantir que a variável message_count é atualizada corretamente

# Inicializar documento dos last IDs se não existir
collection_lastids.replace_one({}, {
    "LastIDMove": 0,
    "LastIDSound": 0
}, upsert=True)

# Ler os valores atuais
doc_last_ids = collection_lastids.find_one({})

# Variáveis globais com os IDs
last_move_id = doc_last_ids.get("LastIDMove", 1)
last_sound_id = doc_last_ids.get("LastIDSound", 1)


# Função para obter o timestamp atual
def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

# Callback quando recebe uma mensagem
def on_message(client, userdata, msg):
    global message_received, last_move_id, last_sound_id
    payload = msg.payload.decode("utf-8")
    print("[Cloud->MongoDB] Mensagem recebida:", payload)

    # Remover os caracteres '{' e '}' do início e do final do payload
    payload = payload.strip("{")
    payload = payload.strip("}")

    # Atualizar contador de mensagens recebidas
    with lock:
        message_received += 1

    # Processar a mensagem conforme o tópico
    if msg.topic == MQTT_MOVE_TOPIC:
        # Exemplo de payload: "Player:15, Marsami:24, RoomOrigin:8, RoomDestiny:9, Status:1"

        fields = payload.split(", ")
        message = {}
        last_move_id += 1
        message["IDMove"] = last_move_id
        for field in fields:
            key, value = field.split(":")
            message[key.strip()] = int(value.strip())

        message["IsMigrated"] = False
        message["Hora"] = get_current_timestamp()
        collection_lastids.update_one({}, {"$set": {"LastIDMove": last_move_id}})

        # Inserir no MongoDB
        collection_move.insert_one(message)
        print("[Cloud->MongoDB] Inserido no MongoDB:", message)
    elif msg.topic == MQTT_SOUND_TOPIC:
        # Exemplo de payload: "Player:15, Hour:2025-03-07 21:04:29.193352, Sound:19.2"

        fields = payload.split(", ")
        message = {}
        last_sound_id += 1
        message["IDSound"] = last_sound_id
        message["Hour"] = get_current_timestamp()
        message["Player"] = int(fields[0].split(":")[1])
        message["Sound"] = fields[2].split(":")[1]
        message["IsMigrated"] = False  
        collection_lastids.update_one({}, {"$set": {"LastIDSound": last_sound_id}})

        # Inserir no MongoDB
        collection_sound.insert_one(message)
        print("[Cloud->MongoDB] Inserido no MongoDB:", message)

# Função para subscrever a um tópico MQTT
def mqtt_subscriber(topic):
    print(f"1. [Cloud->MongoDB] A subscrever ao tópico {topic}...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic, qos=2)
    print(f"2. [Cloud->MongoDB] Subscrito ao tópico {topic}, aguardando mensagens...")
    client.loop_forever()

# Funcao para verificar se as mensagens foram recebidas
def check_messages_received():
    while True:
        time.sleep(10)  # Verificar a cada 10 segundos

        with lock:
            received_count = message_received

        mongo_count_move = collection_move.count_documents({})
        mongo_count_sound = collection_sound.count_documents({})
        total_count = mongo_count_move + mongo_count_sound
        print(f"Mensagens recebidas: {received_count} | Mensagens no MongoDB: {total_count} | Move: {mongo_count_move} | Sound: {mongo_count_sound}")

if __name__ == "__main__":

    # Iniciar threads
    mqtt_thread_move = threading.Thread(target=mqtt_subscriber, args=(MQTT_MOVE_TOPIC,), daemon=True)
    mqtt_thread_sound = threading.Thread(target=mqtt_subscriber, args=(MQTT_SOUND_TOPIC,), daemon=True)
    #check_thread = threading.Thread(target=check_messages_received, daemon=True)  # For debugging

    mqtt_thread_move.start()
    mqtt_thread_sound.start()
    #check_thread.start()

    # Esperar que as threads terminem  [ Não vão terminar por causa do loop_forever() ]
    mqtt_thread_move.join()
    mqtt_thread_sound.join()
    #check_thread.join()