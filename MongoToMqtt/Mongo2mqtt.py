import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
import time
import threading

# Configuração do MongoDB
MONGO_URI = MongoClient("mongodb://localhost:27017/")
MONGO_DB = MONGO_URI["Pisisdtestes"]

MONGO_COLLECTION_MOVE = MONGO_DB["medicoes"]
MONGO_COLLECTION_SOUND = MONGO_DB["sound"]

# Configuração do MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

MQTT_MOVE_TOPIC = "move_grupo15"
MQTT_SOUND_TOPIC = "sound_grupo15"
MQTT_ACK_TOPIC = "ack_grupo15"

# Cliente MQTT
print("[MongoDB->MQTT] Conectando ao broker MQTT...")
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
print("[MongoDB->MQTT] Conectado ao broker MQTT...")

# Handler para ACKs recebidos
def on_message_ack(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        mongoid = int(dados.get("_id_mongoid"))
        collection_name = dados.get("collection")

        if not mongoid or not collection_name:
            print("[MongoDB->MQTT] ACK inválido: faltam campos")
            return


        if collection_name == "medicoes":
            MONGO_COLLECTION_MOVE.update_one({"_id_mongoid": mongoid}, {"$set": {"IsMigrated": True}})
        elif collection_name == "sound":
            MONGO_COLLECTION_SOUND.update_one({"_id_mongoid": mongoid}, {"$set": {"IsMigrated": True}})
        else:
            print(f"[MongoDB->MQTT] Nome de coleção desconhecido: {collection_name}")
            return

        print(f"[MongoDB->MQTT] Marcado como migrado: {mongoid} na coleção {collection_name}")

    except Exception as e:
        print(f"[MongoDB->MQTT] Erro ao processar ACK: {e}")

client.on_message = on_message_ack
client.subscribe(MQTT_ACK_TOPIC)
client.loop_start()

# Publicar apenas documentos que ainda não foram migrados
def publish_data(collection, mqtt_topic, collection_name):
    print(f"[MongoDB->MQTT] A iniciar publicação contínua para o tópico {mqtt_topic}...")
    while True:
        documentos_encontrados = False
        for documento in collection.find({"IsMigrated": {"$ne": True}}):
            documentos_encontrados = True
            mensagem = documento.copy()
            mensagem["_id_mongoid"] = str(mensagem["_id_mongoid"])  # Facilita o parsing do lado do recetor
            mensagem["collection"] = collection_name
            mensagem_json = json.dumps(mensagem, default=str)
            client.publish(mqtt_topic, mensagem_json)
            print(f"[MongoDB->MQTT] Publicado: {mensagem_json}")
            time.sleep(0.3)  # Pequeno atraso para evitar flood

        if not documentos_encontrados:
            print(f"[MongoDB->MQTT] Nenhum novo documento para {collection_name}.")

        time.sleep(5)  # Espera antes de procurar novos documentos novamente

# Início da aplicação
if __name__ == "__main__":
    thread_move = threading.Thread(target=publish_data, args=(MONGO_COLLECTION_MOVE, MQTT_MOVE_TOPIC, "medicoes"))
    thread_sound = threading.Thread(target=publish_data, args=(MONGO_COLLECTION_SOUND, MQTT_SOUND_TOPIC, "sound"))

    thread_move.start()
    thread_sound.start()

    thread_move.join()
    thread_sound.join()

    client.loop_stop()
    client.disconnect()
    print("[MongoDB->MQTT] Finalizado.")
