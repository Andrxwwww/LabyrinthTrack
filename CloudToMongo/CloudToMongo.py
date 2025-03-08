import threading
import queue
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import time
from datetime import datetime

# Configurações MQTT
# mqtt-dashboard.com broker.hivemq.com
MQTT_BROKER = "mqtt-dashboard.com"
MQTT_PORT = 1883
MQTT_MOVE_TOPIC = "pisid_mazemov_15"  # Tópico para obter a info do movimento
MQTT_SOUND_TOPIC = "pisid_mazesound_15"  # Tópico para obter a info do som

# Configurações MongoDB
MONGO_URI = "mongodb://localhost:27017/"  # Ajustar conforme necessário
MONGO_DB = "PISID_Maze"
MONGO_COLLECTION_MOVE = "Move"
MONGO_COLLECTION_SOUND = "Sound"

# Conectar ao MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
collection_move = db[MONGO_COLLECTION_MOVE]
collection_sound = db[MONGO_COLLECTION_SOUND]

# Limpar todas as coleções **REMOVER DEPOIS**
collection_move.delete_many({})
collection_sound.delete_many({})

# Fila para inserir mensagens no MongoDB
message_queue = queue.Queue()

# Contador de mensagens recebidas
message_received = 0
lock = threading.Lock()  # Lock para garantir que a variável message_count é atualizada corretamente

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

# Callback quando recebe uma mensagem
def on_message(client, userdata, msg):
    global message_received
    payload = msg.payload.decode("utf-8")
    print("Mensagem recebida:", payload)

    # Remover os caracteres '{' e '}' do início e do final do payload
    payload = payload.strip("{")
    payload = payload.strip("}")

    # Atualizar contador de mensagens recebidas
    with lock:
        message_received += 1

    # Processar a mensagem conforme o tópico
    if msg.topic == MQTT_MOVE_TOPIC:
        # Exemplo de payload: "Player:15, Marsami:24, RoomOrigin:8, RoomDestiny:9, Status:1"
        # Separar os campos e criar um dicionário
        fields = payload.split(", ")
        message = {}
        for field in fields:
            key, value = field.split(":")
            message[key.strip()] = int(value.strip())
        message["Hora"] = get_current_timestamp() # Possivel erro ?????
        
    elif msg.topic == MQTT_SOUND_TOPIC:
        # Exemplo de payload: "Player:15, Hour:2025-03-07 21:04:29.193352, Sound:19.2"
        # Separar os campos e criar um dicionário
        fields = payload.split(", ")
        message = {}
        message["Player"] = int(fields[0].split(":")[1])
        message["Hour"] = get_current_timestamp() # Possivel erro ?????
        message["Sound"] = fields[2].split(":")[1]
        
    # Inserir na fila para processamento no MongoDB
    message_queue.put((msg.topic, message))

# Função para subscrever a um tópico MQTT
def mqtt_subscriber(topic):
    print(f"1. A subscrever ao tópico {topic}...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic, qos=2)
    print(f"2. Subscrito ao tópico {topic}, aguardando mensagens...")
    client.loop_forever()

# Função para inserir mensagens no MongoDB
def mongo_writer():
    while True:
        topic, message = message_queue.get()
        if topic == MQTT_MOVE_TOPIC:
            collection_move.insert_one(message)
        elif topic == MQTT_SOUND_TOPIC:
            collection_sound.insert_one(message)

        print("Inserido no MongoDB:", message)
        message_queue.task_done()

def check_messages_received():
    while True:
        time.sleep(10)  # Verificar a cada 10 segundos

        with lock:
            received_count = message_received

        mongo_count_move = collection_move.count_documents({})
        mongo_count_sound = collection_sound.count_documents({})
        total_count = mongo_count_move + mongo_count_sound
        print(f"Mensagens recebidas: {received_count} | Mensagens no MongoDB: {total_count} | Move: {mongo_count_move} | Sound: {mongo_count_sound}")

# Iniciar threads
mqtt_thread_move = threading.Thread(target=mqtt_subscriber, args=(MQTT_MOVE_TOPIC,), daemon=True)
mqtt_thread_sound = threading.Thread(target=mqtt_subscriber, args=(MQTT_SOUND_TOPIC,), daemon=True)
mongo_thread = threading.Thread(target=mongo_writer, daemon=True)
check_thread = threading.Thread(target=check_messages_received, daemon=True)

mqtt_thread_move.start()
mqtt_thread_sound.start()
mongo_thread.start()
check_thread.start()

# Esperar que as threads terminem  [ Nao vao terminar por causa do loop_forever() ]
mqtt_thread_move.join()
mqtt_thread_sound.join()
mongo_thread.join()
check_thread.join()