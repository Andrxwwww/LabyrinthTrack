import os
import threading
import paho.mqtt.client as mqtt
import time
from datetime import datetime
import signal

from MongoConfigs import *

#Broker novo:
# > mazerun 15 1 1 20.39.241.21 1883


# Limpar todas as coleções **REMOVER DEPOIS**
collection_move.delete_many({})
collection_sound.delete_many({})
collection_failed.delete_many({})

# Contador de mensagens recebidas
message_received = 0
lock = threading.Lock()
running = True  # Variável de controle para encerramento

# Inicializar documento dos last IDs se não existir
doc_last_ids = collection_lastids.find_one({})
last_move_id = doc_last_ids.get("LastIDMove", 0)
last_sound_id = doc_last_ids.get("LastIDSound", 0)


def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def on_message(client, userdata, msg):
    global message_received, last_move_id, last_sound_id
    payload = msg.payload.decode("utf-8")
    print("[Cloud->MongoDB] Mensagem recebida:", payload)

    payload = payload.strip("{}")

    with lock:
        message_received += 1

    if msg.topic == MQTT_MOVE_TOPIC:
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

        collection_move.insert_one(message)
        print("[Cloud->MongoDB] Inserido no MongoDB:", message)
    elif msg.topic == MQTT_SOUND_TOPIC:
        fields = payload.split(", ")
        message = {}
        last_sound_id += 1
        message["IDSound"] = last_sound_id
        message["Hour"] = get_current_timestamp()
        message["Player"] = int(fields[0].split(":")[1])
        message["Sound"] = fields[2].split(":")[1]
        message["IsMigrated"] = False
        collection_lastids.update_one({}, {"$set": {"LastIDSound": last_sound_id}})

        collection_sound.insert_one(message)
        print("[Cloud->MongoDB] Inserido no MongoDB:", message)


def mqtt_subscriber(topic, num_qos):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"Conectado ao Broker {MQTT_BROKER} no tópico {topic}")
    except Exception as e:
        print(f"[Erro] Conexão ao broker falhou -> {e}")
        return
    client.subscribe(topic, qos=num_qos)
    client.loop_start()  # Inicia o loop em background
    print(f"Subscrito ao tópico {topic}, aguardando mensagens...")

    global running
    while running:
        time.sleep(0.1)  # Mantém a thread ativa verificando a variável 'running'

    client.loop_stop()
    client.disconnect()
    print(f"Desconectado do tópico {topic}")


def check_messages_received():
    while running:
        time.sleep(10)
        with lock:
            received_count = message_received
        mongo_count_move = collection_move.count_documents({})
        mongo_count_sound = collection_sound.count_documents({})
        total_count = mongo_count_move + mongo_count_sound
        print(
            f"Mensagens recebidas: {received_count} | MongoDB: {total_count} (Move: {mongo_count_move}, Sound: {mongo_count_sound})")


def signal_handler(sig, frame):
    global running
    print("\n[INFO] Ctrl+C pressionado. Encerrando...")
    running = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        mqtt_thread_move = threading.Thread(target=mqtt_subscriber, args=(MQTT_MOVE_TOPIC, 2))
        mqtt_thread_sound = threading.Thread(target=mqtt_subscriber, args=(MQTT_SOUND_TOPIC, 1))
        check_thread = threading.Thread(target=check_messages_received)

        mqtt_thread_move.start()
        mqtt_thread_sound.start()
        check_thread.start()

        # Esperar até que todas as threads terminem
        while mqtt_thread_move.is_alive() or mqtt_thread_sound.is_alive() or check_thread.is_alive():
            time.sleep(0.5)

    except Exception as e:
        print(f"[Erro] {e}")
    finally:
        running = False
        print("Programa encerrado.")