from datetime import datetime
import paho.mqtt.client as mqtt
import json
import threading
import time
from decimal import Decimal


##coloar try cach
from BDConfigs import *
from Validations_PC2 import (
    validar_mensagem_move, verificar_outlier , convert_data_for_failedCollection, verificar_variacao_som, validar_data
)

current_game = 0
current_game_lock = threading.Lock()

# Callback para mensagens de SOUND
def on_message_sound(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        print(f"[MQTT->MySQL] Mensagem recebida: {dados}")
        id_sound = dados.get("IDSound") 
        sound = float(Decimal(dados.get("Sound")))
        #print(f"SOM NUMERO: {sound}, TIPO DE VARIAVEL: {type(sound)}")
        hour = dados.get("Hour")

        idjogo = get_idjogo_atual()
        if idjogo is None:
            print("[MQTT->MySQL] Nenhum jogo com estado 'running' encontrado.")
            return

        #createGame(idjogo)

        if verificar_outlier(sound , idjogo): # and not validar_data(hour):
            dados_som = json.dumps(convert_data_for_failedCollection(dados, "5. [Mqtt->MySQL] Outlier detectado", "Sound"))
            client.publish(GROUP_MQTT_FAILED_TOPIC, dados_som)
            print(f"[MQTT->MySQL] Mensagem inválida Sound: {dados}")
            return
        else:
            verificar_variacao_som(idjogo)
            cursor.execute("INSERT INTO sound (IDSound,Sound, IdJogo, Hour) VALUES (%s,%s, %s, %s)", (id_sound,sound, idjogo, hour))
            db.commit()


        print(f"[MQTT->MySQL] Guardado no MySQL (SOUND): {dados}")
        ##enviar o ack para o mongo
        ack_message = json.dumps({
            "IDMongo": id_sound,
            "collection": "Sound"  # identifica a coleção certa
        })
        client.publish(GROUP_MQTT_ACK_TOPIC, ack_message,qos=2) #para garantir que entrega
        print(f"[MQTT->MySQL] Enviado ACK para {id_sound}")

    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao processar mensagem SOUND: {e}")

# Callback para mensagens de MEDIÇÕES
def on_message_medicoes(client, userdata, msg):
    try:

        dados = json.loads(msg.payload.decode())
        id_move = dados.get("IDMove") ## este nome foi só para testes
        marsami = dados.get("Marsami")
        room_origin = dados.get("RoomOrigin")
        room_destiny = dados.get("RoomDestiny")
        status = dados.get("Status")
        hour = dados.get("Hora")

        idjogo = get_idjogo_atual()
        if idjogo is None:
            print("[MQTT->MySQL] Nenhum jogo com estado 'running' encontrado.")
            return

        

        # Para criar a tabela jogos
        #createGame(idjogo)
        if not validar_mensagem_move(dados):
            dados_move = json.dumps(convert_data_for_failedCollection(dados, "4. Mensagem inválida" , "Move"))
            client.publish(GROUP_MQTT_FAILED_TOPIC, dados_move)
            print(f"[MQTT->MySQL] Mensagem inválida Move: {dados}")
            return
        else:
            cursor.execute(
                "INSERT INTO medicoespassagens (IDMedicao,Hora,SalaOrigem,SalaDestino, Marsami,Status,IDJogo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (id_move, hour ,room_origin, room_destiny,marsami,status,idjogo)
            )
            db.commit()
            print(f"[MQTT->MySQL] Guardado no MySQL (MEDIÇÕES): {dados}")
        
        #enviar o ack para o mongo
        ack_message = json.dumps({
            "IDMongo": id_move,
            "collection": "Move"  # ou "sound", conforme a coleção certa
        })
        client.publish(GROUP_MQTT_ACK_TOPIC, ack_message,qos=2)

        #mazeOcupation(marsami, room_origin, room_destiny)

        print(f"[MQTT->MySQL] Enviado ACK para {id_move}")

    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao processar mensagem MEDIÇÕES: {e}")

def createGame(idjogo):
    global current_game
    with current_game_lock:
        if idjogo != current_game:
            current_game = idjogo
            cursor.execute(
                "INSERT INTO jogo (IDJogo) VALUES (%s)",
                (idjogo,)
            )
            db.commit()
            print(f"[MQTT->MySQL] Guardado no MySQL (Jogo): {idjogo}")

## if tabela n exite cria else dá update
def mazeOcupation(marsami, room_origin, room_destiny):
    global current_game

    idjogo = get_idjogo_atual()
    if idjogo is None:
        print("[MQTT->MySQL] Nenhum jogo com estado 'running' encontrado.")
        return

    with current_game_lock:
        if room_origin == 0 and room_destiny == 0:
            # Se origem e destino forem 0, o marsami está preso e não há atualização necessária
            return

        # Verifica se já existe um registo para esta sala e jogo
        cursor.execute("SELECT NumeroMarsamisOdd, NumeroMarsamisEven FROM ocupacaolabirinto WHERE IDJogo = %s AND Sala = %s",
                       (idjogo, room_destiny))
        result_destiny = cursor.fetchone()

        if result_destiny is None:
            # Se não existir, insere um novo registo na sala de destino
            if marsami % 2:
                cursor.execute("INSERT INTO ocupacaolabirinto (IDJogo, NumeroMarsamisOdd, Sala) VALUES (%s, %s, %s)",
                               (idjogo, 1, room_destiny))
            else:
                cursor.execute("INSERT INTO ocupacaolabirinto (IDJogo, NumeroMarsamisEven, Sala) VALUES (%s, %s, %s)",
                               (idjogo, 1, room_destiny))
        else:
            # Se já existir, atualiza os valores na sala de destino
            if marsami % 2:
                cursor.execute("UPDATE ocupacaolabirinto SET NumeroMarsamisOdd = NumeroMarsamisOdd + 1 WHERE IDJogo = %s AND Sala = %s",
                               (idjogo, room_destiny))
            else:
                cursor.execute("UPDATE ocupacaolabirinto SET NumeroMarsamisEven = NumeroMarsamisEven + 1 WHERE IDJogo = %s AND Sala = %s",
                               (idjogo, room_destiny))

        # Se a sala de origem não for 0, decrementa o contador da sala de origem
        if room_origin != 0:
            cursor.execute("SELECT NumeroMarsamisOdd, NumeroMarsamisEven FROM ocupacaolabirinto WHERE IDJogo = %s AND Sala = %s",
                           (idjogo, room_origin))
            result_origin = cursor.fetchone()

            if result_origin:
                if marsami % 2:
                    cursor.execute(
                        "UPDATE ocupacaolabirinto SET NumeroMarsamisOdd = NumeroMarsamisOdd - 1 WHERE IDJogo = %s AND Sala = %s",
                        (idjogo, room_origin))
                else:
                    cursor.execute(
                        "UPDATE ocupacaolabirinto SET NumeroMarsamisEven = NumeroMarsamisEven - 1 WHERE IDJogo = %s AND Sala = %s",
                        (idjogo, room_origin))

        # Confirma a alteração na base de dados
        db.commit()
        print("Atualizada as alterarçoes do labirinto")

def get_idjogo_atual():
    try:
        cursor.execute("SELECT IDJogo FROM jogo WHERE Estado = 'running' ORDER BY IDJogo DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None  # Ou lança exceção, dependendo do comportamento desejado
    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao obter IDJogo atual: {e}")
        return None


def keep_alive_sender():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    while True:
        try:
            # Verificar se a conexão à base de dados está viva
            db.ping()

            # Se não levantar exceção, envia mensagem de keep alive
            keep_alive_message = json.dumps({
                "status": "alive",
                "timestamp": datetime.now().isoformat()
            })
            client.publish("keep_alive", keep_alive_message)
            print("[MQTT->MySQL] Mensagem Keep Alive enviada.")

        except mariadb.Error as e:
            print(f"[MQTT->MySQL] Ligação à base de dados perdida: {e}")
            reconnect_db()
            continue

        time.sleep(2)  # Espera 30 segundos

    client.loop_stop()
    client.disconnect()
    print("[MQTT->MySQL] Keep Alive thread terminada.")

def reconnect_db():
    global db, cursor
    try:
        db.close()  # Tenta fechar qualquer ligação antiga
    except:
        pass

    connected = False
    while not connected:
        try:
            db = mariadb.connect(
                host="127.0.0.1",
                user="root",
                password="",
                database="pisid_sql"
            )
            cursor = db.cursor()
            connected = True
            print("[MQTT->MySQL] Reconectado com sucesso ao MySQL.")
        except mariadb.Error as e:
            print(f"[MQTT->MySQL] Erro ao reconectar ao MySQL: {e}")
            time.sleep(10)


# Função para criar um cliente MQTT numa thread
def start_mqtt_client(topic, on_message_callback):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message_callback
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic)
    client.subscribe(GROUP_MQTT_FAILED_TOPIC)
    print(f"[MQTT->MySQL] A ouvir mensagens MQTT no tópico {topic}...")
    client.loop_forever()

if __name__ == "__main__":
    # Criar duas threads para os dois tópicos
    thread_sound = threading.Thread(target=start_mqtt_client, args=(GROUP_MQTT_SOUND_TOPIC, on_message_sound))
    thread_medicoes = threading.Thread(target=start_mqtt_client, args=(GROUP_MQTT_MOVE_TOPIC, on_message_medicoes))

    # Criar thread para o keep_alive
    thread_keep_alive = threading.Thread(target=keep_alive_sender)

    # Iniciar as threads
    thread_sound.start()
    thread_medicoes.start()
    thread_keep_alive.start()



    # Esperar as threads terminarem (caso seja necessário)
    thread_sound.join()
    thread_medicoes.join()
    thread_keep_alive.join()
