import paho.mqtt.client as mqtt
import json
import time
import threading


from MongoConfigs import *
from Validations_PC1 import *

#Keep_alive
from datetime import datetime, timedelta

last_keep_alive = datetime.now()
keep_alive_lock = threading.Lock()


# Cliente MQTT
print("[MongoDB->MQTT] Conectando ao broker MQTT...")
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
print("[MongoDB->MQTT] Conectado ao broker MQTT...")

# Handler para ACKs recebidos
def on_message_ack(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        print(f"[MongoDB->MQTT] ACK recebido: {dados}")
        collection_name = dados.get("collection")
        print(f"[MongoDB->MQTT] Nome da coleção: {collection_name}")

        if collection_name == "Move":
            id_move = dados.get("IDMongo")
            collection_move.update_one({"IDMove": id_move}, {"$set": {"IsMigrated": True}})
            print(f"[MongoDB->MQTT] IDMove: {id_move} atualizado para IsMigrated: True")

        elif collection_name == "Sound":
            id_sound = dados.get("IDMongo")
            collection_sound.update_one({"IDSound": id_sound}, {"$set": {"IsMigrated": True}})
            print(f"[MongoDB->MQTT] IDSound: {id_sound} atualizado para IsMigrated: True")

        else:
            print(f"[MongoDB->MQTT] Nome de coleção desconhecido: {collection_name}")

    except Exception as e:
        print(f"[MongoDB->MQTT] Erro ao processar ACK: {e}")

def on_message_failed(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        print(f"[MongoDB->MQTT] Mensagem recebida no tópico FAILED: {dados}")


        if dados.get("Collection") == "Sound":
            collection_sound.update_one({"IDSound": dados.get("IDMessage") }, {"$set": {"IsMigrated": True}})
            collection_failed.insert_one(dados)
            #collection_sound.delete_one({"IDSound": dados.get("IDMessage")})
        elif dados.get("Collection") == "Move":
            collection_move.update_one({"IDMove": dados.get("IDMessage")}, {"$set": {"IsMigrated": True}})
            collection_failed.insert_one(dados)
            #collection_move.delete_one({"IDMove": IDMessage})

        print(f"A COLECAO É: {dados.get('Collection')}")
        print(f"[MongoDB->MQTT] Documento inserido na coleção 'Failed'")
        
    except Exception as e:
        print(f"[MongoDB->MQTT] Erro ao processar mensagem do tópico FAILED: {e}")


def on_message(client, userdata, msg):
    global last_keep_alive

    if msg.topic == GROUP_MQTT_Alive_TOPIC:
        with keep_alive_lock:
            last_keep_alive = datetime.now()
        print("[MongoDB->MQTT] Keep Alive recebido.")
    if msg.topic == GROUP_MQTT_FAILED_TOPIC:
        on_message_failed(client, userdata, msg)
    elif msg.topic == GROUP_MQTT_ACK_TOPIC:
        on_message_ack(client, userdata, msg)
    else:
        print(f"[MongoDB->MQTT] Mensagem recebida num tópico não tratado: {msg.topic}")

client.on_message = on_message
client.subscribe(GROUP_MQTT_FAILED_TOPIC, qos=2)
client.subscribe(GROUP_MQTT_ACK_TOPIC, qos=2)
client.subscribe("keep_alive", qos=1)
client.loop_start()


# Publicar apenas documentos que ainda não foram migrados
def publish_data(collection, mqtt_topic):
    print(f"[MongoDB->MQTT] A iniciar publicação contínua para o tópico {mqtt_topic}...")
    #Verifica se o MySql esta a enviar msg
    while True:
        #with keep_alive_lock:
        #    tempo_desde_ultimo_keep_alive = datetime.now() - last_keep_alive

        #if tempo_desde_ultimo_keep_alive > timedelta(seconds=15):
        #    print(f"[MongoDB->MQTT] Sem keep alive há {tempo_desde_ultimo_keep_alive.seconds}s. Publicação pausada.")
        #    time.sleep(5)
        #    continue
        documentos_encontrados = False
        for documento in collection.find({"IsMigrated": {"$ne": True}}):
            documentos_encontrados = True
            mensagem = documento.copy()

            if mqtt_topic == GROUP_MQTT_MOVE_TOPIC:
                if validar_movimento(documento):
                    mensagem_json = json.dumps(mensagem, default=str)
                    print(f"[MongoDB->MQTT] Publicado Move (VALIDADO): {mensagem_json}")
                    client.publish(mqtt_topic, mensagem_json)
                else:
                    collection_move.update_one({"IDMove": documento.get("IDMove")}, {"$set": {"IsMigrated": True}})
                    collection_failed.insert_one(convert_data_for_failedCollection(documento,"2.[Mongo->MQTT] Movimento Invalido","Move"))  # Guardar na coleção Failed
                    print(f"[MongoDB->MQTT] Documento Move (INVÁLIDO) guardado em 'Failed': {documento}")

            elif mqtt_topic == GROUP_MQTT_SOUND_TOPIC:
                if validar_sound(documento):
                    mensagem_json = json.dumps(mensagem, default=str)
                    print(f"[MongoDB->MQTT] Publicado Sound (VALIDADO): {mensagem_json}")
                    client.publish(mqtt_topic, mensagem_json)
                else:
                    collection_sound.update_one({"IDSound": documento.get("IDSound")}, {"$set": {"IsMigrated": True}})
                    collection_failed.insert_one(convert_data_for_failedCollection(documento,"3.[Mongo->MQTT] Som Invalido","Sound"))
                    print(f"[MongoDB->MQTT] Documento Sound (INVÁLIDO) guardado em 'Failed': {documento}")

            else:
                print(f"[MongoDB->MQTT] Tópico desconhecido: {mqtt_topic}")

            time.sleep(1) 

        if not documentos_encontrados:
            print(f"[MongoDB->MQTT] Nenhum novo documento .")

        time.sleep(5)  # Espera antes da próxima verificação


# Início da aplicação
if __name__ == "__main__":
    thread_move = threading.Thread(target=publish_data, args=(collection_move, GROUP_MQTT_MOVE_TOPIC))
    thread_sound = threading.Thread(target=publish_data, args=(collection_sound, GROUP_MQTT_SOUND_TOPIC))

    thread_move.start()
    thread_sound.start()

    thread_move.join()
    thread_sound.join()

    client.loop_stop()
    client.disconnect()
    print("[MongoDB->MQTT] Finalizado.")

# dar update de true para false pelo mongocompass
#{
#  "$set": {
#    "IsMigrated": false
#  }
#}