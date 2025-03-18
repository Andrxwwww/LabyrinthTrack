import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
import time
import threading

# Configuração do MongoDB
MONGO_URI = MongoClient("mongodb://localhost:27017/")
MONGO_DB = MONGO_URI["PISID_Maze"]

MONGO_COLLECTION_MOVE = MONGO_DB["Move"]
MONGO_COLLECTION_SOUND = MONGO_DB["Sound"]

# Configuração do MQTT
# mqtt-dashboard.com broker.hivemq.com broker.emqx.io
MQTT_BROKER = "mqtt-dashboard.com"  # Altere para o endereço do teu broker MQTT
MQTT_PORT = 1883

MQTT_MOVE_TOPIC = "move_grupo15"
MQTT_SOUND_TOPIC = "sound_grupo15"

print("[MongoDB->MQTT] Conectando ao broker MQTT...")
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
print("[MongoDB->MQTT] Conectado ao broker MQTT...")

# Função para publicar dados
def publish_data(collection, mqtt_topic):
    print(f"[MongoDB->MQTT] A iniciar publicacao para o topico {mqtt_topic}...")
    for documento in collection.find():
        mensagem = json.dumps(documento, default=str)  # Converte para JSON
        client.publish(mqtt_topic, mensagem)
        print(f"[MongoDB->MQTT] Publicado: {mensagem}")

if __name__ == "__main__":

    # Criar threads para publicar os dados de ambas as coleções
    thread_move = threading.Thread(target=publish_data, args=(MONGO_COLLECTION_MOVE, MQTT_MOVE_TOPIC))
    thread_sound = threading.Thread(target=publish_data, args=(MONGO_COLLECTION_SOUND, MQTT_SOUND_TOPIC))

    # Iniciar as threads
    thread_move.start()
    thread_sound.start()

    # Esperar as threads terminarem
    thread_move.join()
    thread_sound.join()
    
    client.loop_stop()
    client.disconnect()
