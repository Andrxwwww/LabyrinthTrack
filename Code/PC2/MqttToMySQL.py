import os
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import json
import threading
import time
from decimal import Decimal
import statistics
import mariadb
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import signal


import paho.mqtt.client as mqtt

import threading
import time

# ... (outros imports e configurações permanecem iguais)

# Configurações e inicializações de banco de dados
# (Mantidas do código original com ajustes de formatação)
from BDConfigs import *
from BDdata_PC2 import *
import MySQLToMySQL
MySQLToMySQL.main()

# Variáveis globais
current_game = 0
db_lock = threading.Lock()
current_game_lock = threading.Lock()

# Estruturas para processamento paralelo
message_queue = Queue()
executor = ThreadPoolExecutor(max_workers=4)  # Ajuste conforme necessidade

# Variável global de controle
running = True


def signal_handler(sig, frame):
    global running
    print("\n[INFO] Ctrl+C pressionado. Encerrando...")
    running = False


# Modificação na função queue_consumer
def queue_consumer():
    global running
    while running:
        try:
            topic, payload = message_queue.get(timeout=1)
            if topic == GROUP_MQTT_SOUND_TOPIC:
                executor.submit(process_sound_message, payload)
            elif topic == GROUP_MQTT_MOVE_TOPIC:
                executor.submit(process_move_message, payload)
            message_queue.task_done()
        except Exception as e:
            if running:  # Só mostra erros se ainda estiver rodando
                print(f"[Consumer] Erro no consumer: {e}")
        time.sleep(0.01)


# Modificação na função keep_alive_sender
def keep_alive_sender():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Conectado ao MQTT " + MQTT_BROKER)
    client.loop_start()

    global running
    while running:
        try:
            # ... (código original mantido)
            time.sleep(2)
        except Exception as e:
            print(f"[Keep Alive] Erro: {e}")

    client.loop_stop()
    client.disconnect()


# Modificação na função start_mqtt_client
def start_mqtt_client():
    global client_mqtt, running
    try:
        client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client_mqtt.on_message = on_message
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        client_mqtt.subscribe([
            (GROUP_MQTT_SOUND_TOPIC, 2),
            (GROUP_MQTT_MOVE_TOPIC, 2)
        ])
        print("[MQTT] Conectado e inscrito em todos os tópicos")

        while running:
            client_mqtt.loop(timeout=1.0)

    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao iniciar cliente MQTT: {e}")
    finally:
        client_mqtt.disconnect()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Threads principais
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    consumer_thread = threading.Thread(target=queue_consumer)
    keep_alive_thread = threading.Thread(target=keep_alive_sender)

    mqtt_thread.start()
    consumer_thread.start()
    keep_alive_thread.start()

    try:
        while running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[MQTT->MySQL] Encerrando...")
        running = False

        # Esperar threads
        mqtt_thread.join(timeout=5)
        consumer_thread.join(timeout=5)
        keep_alive_thread.join(timeout=5)

        # Limpeza final
        executor.shutdown(wait=True)
        try:
            db.close()
            print("[MySQL] Conexão fechada")
        except:
            pass
        print("Encerramento completo.")