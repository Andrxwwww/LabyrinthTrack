from datetime import datetime
import paho.mqtt.client as mqtt
import mariadb
import json
import threading

current_game = 0
current_game_lock = threading.Lock()

# Configuração do MySQL
db = mariadb.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="pisid_sql"
)
cursor = db.cursor()

# Configuração do MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_SOUND_TOPIC = "sound_grupo15"
MQTT_MOVE_TOPIC = "move_grupo15"
MQTT_ACK_TOPIC = "ack_grupo15"
MQTT_FAILED_TOPIC = "failed_grupo15"

# Obter uma constante (config) a partir do MySQL
def get_config(chave):
    cursor.execute("SELECT valor FROM configs WHERE chave = %s", (chave,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        raise ValueError(f"[MQTT->MySQL] Configuração '{chave}' não encontrada.")

# Função para validar mensagens de movimento
# TODO: Falta o MongoToMQTT receber as mensagens que estão nesse topico
def validar_mensagem_move(doc):

    status_ok = int(get_config("status_tudoOK"))
    status_fail = int(get_config("status_nenhuma_porta"))
    status_cansado = int(get_config("status_cansado"))
    sala_min = int(get_config("num_sala_min"))
    sala_max = int(get_config("num_sala_max"))

    origem = doc.get("RoomOrigin")
    destino = doc.get("RoomDestiny")
    status = doc.get("Status")

    # Validação 4: Sala origem igual ao mínimo e destino dentro do intervalo, status OK
    if (origem == sala_min or sala_min < destino <= sala_max) and status == status_ok:
        return True
    # Validação 5: Origem e destino iguais ao mínimo, status é "nenhuma porta" ou "cansado"
    if (origem == sala_min or destino == sala_min) and status in [status_fail, status_cansado]:
        return True
    # Validação 6: Origem e destino dentro do intervalo, status OK
    if (sala_min < origem <= sala_max or sala_min < destino <= sala_max) and status == status_ok:
        return True
    
    return False


# Callback para mensagens de SOUND
def on_message_sound(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
        id_sound = dados.get("IDSound")  #
        sound = dados.get("Sound")
        hour = dados.get("Hour")
        idjogo = 1  # Hardcoded

        createGame(idjogo)

        cursor.execute("INSERT INTO sound (IDSound,Sound, IdJogo, Hour) VALUES (%s,%s, %s, %s)", (id_sound,sound, idjogo, hour))
        db.commit()
        print(f"[MQTT->MySQL] Guardado no MySQL (SOUND): {dados}")
        ##enviar o ack para o mongo
        ack_message = json.dumps({
            "IDMongo": id_sound,
            "collection": "Sound"  # identifica a coleção certa
        })
        client.publish(MQTT_ACK_TOPIC, ack_message)
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
        idjogo = 1  # Hardcoded

        # Para criar a tabela jogos
        createGame(idjogo)
        if not validar_mensagem_move(dados):
            client.publish(MQTT_FAILED_TOPIC, json.dumps(dados))
            print(f"[MQTT->MySQL] Mensagem inválida: {dados}")
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
        client.publish(MQTT_ACK_TOPIC, ack_message)

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

    idjogo = 1  # Hardcoded

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

# Função para criar um cliente MQTT numa thread
def start_mqtt_client(topic, on_message_callback):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message_callback
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic)
    print(f"[MQTT->MySQL] A ouvir mensagens MQTT no tópico {topic}...")
    client.loop_forever()

if __name__ == "__main__":
    # Criar duas threads para os dois tópicos
    thread_sound = threading.Thread(target=start_mqtt_client, args=(MQTT_SOUND_TOPIC, on_message_sound))
    thread_medicoes = threading.Thread(target=start_mqtt_client, args=(MQTT_MOVE_TOPIC, on_message_medicoes))

    # Iniciar as threads
    thread_sound.start()
    thread_medicoes.start()

    # Esperar as threads terminarem (caso seja necessário)
    thread_sound.join()
    thread_medicoes.join()
