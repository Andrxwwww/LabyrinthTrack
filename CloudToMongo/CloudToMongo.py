import threading
import queue
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import time
from datetime import datetime

# Configurações MQTT
# mqtt-dashboard.com broker.hivemq.com broker.emqx.io
MQTT_BROKER = "mqtt-dashboard.com"
MQTT_PORT = 1883
MQTT_MOVE_TOPIC = "pisid_mazemov_15"  # Tópico para obter a info do movimento
MQTT_SOUND_TOPIC = "pisid_mazesound_15"  # Tópico para obter a info do som

# Configurações MongoDB
MONGO_URI = "mongodb://localhost:23019/"  # Ajustar conforme necessário
MONGO_DB = "PISID_Maze"
MONGO_COLLECTION_MOVE = "Move"
MONGO_COLLECTION_SOUND = "Sound"

# Diretórios para guardar os IDs
Dir_IDMove = "./CloudToMongo/IDs/IDMove.txt"
Dir_IDSound = "./CloudToMongo/IDs/IDSound.txt"
Dir_IDGame = "./CloudToMongo/IDs/IDGame.txt"

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

# Variável para guardar o último múltiplo de 30 verificado
last_multiple = 0

# Função para ler o último ID de um ficheiro
def read_last_id(filename):
    try:
        with open(filename,"r") as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return 1

# Função para escrever o último ID num ficheiro
def write_last_id(filename, id):
    with open(filename,"w") as file:
        file.write(str(id))

# CLEANUP: Remover depois
write_last_id(Dir_IDMove, 0)
write_last_id(Dir_IDSound, 0)
write_last_id(Dir_IDGame, 1)

# Ler o último IDGame de um ficheiro
last_move_id = read_last_id(Dir_IDMove)
last_sound_id = read_last_id(Dir_IDSound)
IDGame = read_last_id(Dir_IDGame)

# Função para obter o timestamp atual
def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

# Função para verificar se o número de Marsamis com Status: 2 é divisível por 30
# FIXME: só funciona para o broker do dashboard e ninguem pode estar a rodar o jogo ao mesmo tempo
# FIXME: o numero de marsamis está um bocado hardcoded
def new_game():
    global IDGame, last_multiple

    while True:
        time.sleep(5)  # Verificar a cada 5 segundos

        # Contar o número de documentos com Status: 2
        count = collection_move.count_documents({"Status": 2})

        # Verificar se o número de documentos é maior que o último múltiplo de 30
        if count > last_multiple and count % 30 == 0:
            IDGame += 1  # Incrementar o IDGame
            write_last_id(Dir_IDGame, IDGame)
            last_multiple = count  # Atualizar o último múltiplo verificado
            print(f"Novo jogo detectado! IDGame: {IDGame}")

# Callback quando recebe uma mensagem
def on_message(client, userdata, msg):
    global message_received, last_move_id, last_sound_id, IDGame
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
        last_move_id += 1
        message["IDGame"] = IDGame
        message["IDMove"] = last_move_id
        for field in fields:
            key, value = field.split(":")
            message[key.strip()] = int(value.strip())

        message["Hora"] = get_current_timestamp() # Possivel erro ?????
        write_last_id(Dir_IDMove, last_move_id)
    elif msg.topic == MQTT_SOUND_TOPIC:
        # Exemplo de payload: "Player:15, Hour:2025-03-07 21:04:29.193352, Sound:19.2"
        # Separar os campos e criar um dicionário
        fields = payload.split(", ")
        message = {}
        last_sound_id+=1
        message["IDGame"] = IDGame
        message["IDSound"] = last_sound_id
        message["Hour"] = get_current_timestamp() # Possivel erro ?????
        message["Player"] = int(fields[0].split(":")[1])
        message["Sound"] = fields[2].split(":")[1]
        write_last_id(Dir_IDSound, last_sound_id)
        
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
check_thread = threading.Thread(target=check_messages_received, daemon=True) # To debugging
new_game_thread = threading.Thread(target=new_game, daemon=True)

mqtt_thread_move.start()
mqtt_thread_sound.start()
mongo_thread.start()
check_thread.start()
new_game_thread.start()

# Esperar que as threads terminem  [ Nao vao terminar por causa do loop_forever() ]
mqtt_thread_move.join()
mqtt_thread_sound.join()
mongo_thread.join()
check_thread.join()
new_game_thread.join()