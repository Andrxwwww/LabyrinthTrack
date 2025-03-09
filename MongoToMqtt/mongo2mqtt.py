import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
import time
import threading

# Configuração do MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["Pisisdtestes"]

# Coleções a serem enviadas
collection1 = db["medicoes"]
collection2 = db["sound"]

# Configuração do MQTT
mqtt_broker = "broker.emqx.io"  # Altere para o endereço do teu broker MQTT
mqtt_port = 1883
##colecões a enviar
mqtt_topic_1 = "dadosmongodb/medicoes"
mqtt_topic_2 = "dadosmongodb/sound"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(mqtt_broker, mqtt_port, 60)


# Função para publicar dados
def publicar_dados(collection, mqtt_topic):
    for documento in collection.find():
        mensagem = json.dumps(documento, default=str)  # Converte para JSON
        client.publish(mqtt_topic, mensagem)
        print(f"Publicado: {mensagem}")
        time.sleep(1)  # Pequeno intervalo entre envios


if __name__ == "__main__":
    # Criar threads para publicar os dados de ambas as coleções
    thread1 = threading.Thread(target=publicar_dados, args=(collection1, mqtt_topic_1))
    thread2 = threading.Thread(target=publicar_dados, args=(collection2, mqtt_topic_2))

    # Iniciar as threads
    thread1.start()
    thread2.start()

    # Esperar as threads terminarem
    thread1.join()
    thread2.join()

    client.loop_stop()
    client.disconnect()
