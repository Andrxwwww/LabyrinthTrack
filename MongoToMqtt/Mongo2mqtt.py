from datetime import datetime
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
import time
import threading
from contextlib import closing
import pymysql

# Configuração do MQTT
# mqtt-dashboard.com broker.hivemq.com broker.emqx.io
MQTT_BROKER = "broker.emqx.io"  # Altere para o endereço do teu broker MQTT
MQTT_PORT = 1883
MQTT_MOVE_TOPIC = "move_grupo15"
MQTT_SOUND_TOPIC = "sound_grupo15"
MQTT_ACK_TOPIC = "ack_grupo15"

# CONSTANTES da Configuração do MongoDB
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "PISID_Maze"   #alterar para o nome da base de dados
MONGO_COLLECTION_MOVE = "Move"
MONGO_COLLECTION_SOUND = "Sound"
MONGO_COLLECTION_FAILED = "Failed"  # Coleção para guardar os dados que falharam a inserção

# Conectar ao MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
collection_move = db[MONGO_COLLECTION_MOVE]
collection_sound = db[MONGO_COLLECTION_SOUND]
collection_failed = db[MONGO_COLLECTION_FAILED]  # Coleção para guardar os dados que falharam a inserção

# Função para buscar um campo específico de uma tabela
def getValueFromTableAndColumn(table, column):
    try:
        with closing(pymysql.connect(
            host="194.210.86.10",
            user="aluno",
            password="aluno",
            database="maze",
            cursorclass=pymysql.cursors.DictCursor
        )) as cloud_conn:
            with closing(cloud_conn.cursor()) as cloud_cursor:
                query = f"SELECT `{column}` FROM `{table}` LIMIT 1"
                cloud_cursor.execute(query)
                result = cloud_cursor.fetchone()
                if result and column in result:
                    return result[column]
                else:
                    print(f"Coluna '{column}' não encontrada ou sem dados.")
                    return None
    except Exception as e:
        print(f"Erro ao conectar à base de dados na nuvem: {e}")
        return None

# Função para verificar se dois valores existem como par Rooma/Roomb
def verifyMovimentoValido(roomOrigin, roomDestiny):

    # Spawn de Marsamis e cansaço de marsamis
    if (roomOrigin == 0 and roomDestiny != 0 ) or ( roomOrigin == 0 and roomDestiny == 0 ):
        return True
    
    try:
        with closing(pymysql.connect(
            host="194.210.86.10",
            user="aluno",
            password="aluno",
            database="maze",
            cursorclass=pymysql.cursors.DictCursor
        )) as conn:
            with closing(conn.cursor()) as cursor:
                query = """
                    SELECT * FROM corridor
                    WHERE Rooma = %s AND Roomb = %s
                """
                cursor.execute(query, (roomOrigin, roomDestiny))
                resultado = cursor.fetchone()
                return resultado is not None
    except Exception as e:
        print(f"Erro ao conectar ou consultar a base de dados: {e}")
        return False

#TODO: VALIDAR AS MENSAGENS DE MOVIMENTO EM SI E FAZER NO MQTT->MONGODB
def validar_movimento(doc):
    try:
        marsami = int(doc.get("Marsami"))
        origem = doc.get("RoomOrigin")
        destino = doc.get("RoomDestiny")
        status = doc.get("Status")
        hora = doc.get("Hora")

        # Validação 1: Verificar se os tipos estão corretos antes de fazer a comparação
        if not isinstance(origem, int) or not isinstance(destino, int) or not isinstance(status, int) or not isinstance(marsami, int):
            print(f"[VALIDAÇÃO] Tipos incompatíveis: origem={type(origem)}, destino={type(destino)}, status={type(status)}, marsami={type(marsami)}")
            return False
        
        # Validacao 2: Verificar se os marsamis são válidos
        if marsami is None or marsami < 1 or marsami > getValueFromTableAndColumn("SetupMaze", "numbermarsamis"):
            print(f"[VALIDAÇÃO] Marsami inválido: {marsami}")
            return False
        
        # Validação 3: Varificar o formato da Hora
        try:
            datetime.strptime(hora, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            print(f"[VALIDAÇÃO] Formato de hora inválido: {hora}")
            return False
        
        # Validacao 4: Verificar se os Rooms são válidos
        if origem is None or destino is None or origem < 0 or origem > getValueFromTableAndColumn("SetupMaze", "numberrooms") or destino < 0 or destino > getValueFromTableAndColumn("SetupMaze", "numberrooms"):
            print(f"[VALIDAÇÃO] Rooms inválidos: origem={origem}, destino={destino}")
            return False
        
        # Validação 4: Verificar se o movimento é válido
        if not verifyMovimentoValido(origem, destino):
            print(f"[VALIDAÇÃO] Movimento inválido: {origem} -> {destino}")
            return False

        return True

    except Exception as e:
        print(f"[VALIDAÇÃO] Erro ao validar documento: {e}")
        return False

def validar_sound(doc):
    try:
        hour = doc.get("Hour")
        sound = doc.get("Sound")

        # Validação 1: Verificar se o formato de hora está correto
        try:
            # Tentar converter o formato da hora
            datetime.strptime(hour, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            print(f"[VALIDAÇÃO] Formato de hora inválido: {hour}")
            return False

        # Validação 2: Verificar se o valor de Sound é um número válido (float)
        try:
            sound_value = float(sound)  # Converte a string para float
        except ValueError:
            print(f"[VALIDAÇÃO] Valor de Sound inválido: {sound}")
            return False

        # Validação 3: Verificar se o valor de Sound é um número inteiro (se necessário)
        if not isinstance(sound_value, (int, float)):
            print(f"[VALIDAÇÃO] Tipo inválido para Sound: {type(sound_value)}")
            return False
        
        # Validacao 4: Verificar se o valor de Sound nao é negativo 
        if sound_value < 0:
            print(f"[VALIDAÇÃO] Valor de Sound negativo: {sound_value}")
            return False

        return True

    except Exception as e:
        print(f"[VALIDAÇÃO] Erro ao validar documento Sound: {e}")
        return False

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
            mensagem["_id_mongoid"] = str(mensagem["_id_mongoid"])
            mensagem["collection"] = collection_name

            publicar = False
            if mqtt_topic == MQTT_MOVE_TOPIC:
                if validar_movimento(documento):
                    publicar = True
                else:
                    collection_failed.insert_one(documento)
                    print(f"[MongoDB->MQTT] Documento inválido (MOVE) guardado em 'Failed': {documento}")

            elif mqtt_topic == MQTT_SOUND_TOPIC:
                if validar_sound(documento):
                    publicar = True
                else:
                    collection_failed.insert_one(documento)
                    print(f"[MongoDB->MQTT] Documento inválido (SOUND) guardado em 'Failed': {documento}")

            else:
                publicar = True  # Sem validação para outros tópicos

            if publicar:
                mensagem_json = json.dumps(mensagem, default=str)
                client.publish(mqtt_topic, mensagem_json)
                print(f"[MongoDB->MQTT] Publicado: {mensagem_json}")
                time.sleep(0.3)  # Delay para evitar flood

        if not documentos_encontrados:
            print(f"[MongoDB->MQTT] Nenhum novo documento para {collection_name}.")

        time.sleep(5)  # Espera antes da próxima verificação


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
