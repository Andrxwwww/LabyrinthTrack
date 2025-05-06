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

# Função para validar datas
def validar_data(data):

    # Verifica se a data está no formato correto
    try:
        datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        print(f"[MQTT->MySQL] Data inválida: {data}.")
        return False

    # Validação 4: Verifica se a data está atual e no intervalo correto
    datetime_obj = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
    data_atual = datetime.now()
    threshold = timedelta(minutes=DATETIME_THRESHOLD)
    if datetime_obj < data_atual - threshold or datetime_obj > data_atual + threshold:
        print(f"[MQTT->MySQL] Data fora do intervalo: {data}.")
        return False

    return True


# Função para validar mensagens de movimento
# TODO: Falta o MongoToMQTT receber as mensagens que estão nesse topico
def validar_mensagem_move(doc):

    origem = doc.get("RoomOrigin")
    destino = doc.get("RoomDestiny")
    status = doc.get("Status")
    Hora = doc.get("Hora")

    # Validação 4: Sala origem igual ao mínimo e destino dentro do intervalo, status OK
    if (origem == sala_min or sala_min < destino <= sala_max) and status == status_ok:
        return True

    # Validação 5: Origem e destino iguais ao mínimo, status é "nenhuma porta" ou "cansado"
    if (origem == sala_min or destino == sala_min) and status in [status_fail, status_cansado]:
        return True

    # Validação 6: Origem e destino dentro do intervalo, status OK
    if (sala_min < origem <= sala_max or sala_min < destino <= sala_max) and status == status_ok:
        return True

    # TODO: DEPOIS TIRAR PARA DADOS MAIS RECENTES
    # Validação 7: Verificar se a data está dentro do intervalo
    #if not validar_data(Hora):
    #   return False

    return False



# Funcao para verificar se é outlier ou nao
def verificar_outlier(sound_value , idjogo):

    limite = NOISEVARTOL * LIMITE_DESVIO_PADRAO  # Limite para considerar um valor como outlier

    # Obter os últimos 4 valores válidos do som para o jogo
    cursor.execute("""
        SELECT Sound FROM sound 
        WHERE IdJogo = %s 
        ORDER BY Hour DESC 
        LIMIT 20
    """, (idjogo,))

    resultados = cursor.fetchall()
    historico = []

    for row in resultados:
        valor = float(row[0])
        if len(historico) >= QTD_VALS_SOUND_MAX:
            break
        if len(historico) >= QTD_VALS_SOUND_MIN:
            media = statistics.mean(historico)
            if abs(valor - media) > limite:
                continue  # Ignora valores que seriam outliers
        historico.append(valor)

    if len(historico) < QTD_VALS_SOUND_MIN:
        # Se só temos 1 ou nenhum valor válido, não é possível comparar com confiança
        return False

    media = statistics.mean(historico)
    return abs(sound_value - media) > limite

def verificar_variacao_som(sound_value,id_sound, hour, idjogo):

    VARTOL_80 = NOISEVARTOL * LIMITE_80
    VARTOL_90 = NOISEVARTOL * LIMITE_90

    S80_LIMIT_NOISE = NORMALNOISE + VARTOL_80
    S90_LIMIT_NOISE = NORMALNOISE + VARTOL_90

    try:
        ultimo = float(Decimal(sound_value))
    except (ValueError, TypeError, InvalidOperation) as e:
        print(f"[Mqtt -> MySQL] Erro ao converter valores de som: {e}")
        return

    #variacao = abs(ultimo - penultimo)
    #print(variacao)
    print(ultimo)
    print(S80_LIMIT_NOISE)
    print(S90_LIMIT_NOISE)

    if ultimo >= S90_LIMIT_NOISE:
        print("[Mqtt -> MySQL] Variação do som a 90% do limite.")
        print(f"[Mqtt -> MySQL] FECHAR PORTAS ASAP")

        with db_lock:
            try:
                cursor.execute(
                    "INSERT INTO mensagens (ID, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita, IdJogo) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (id_sound, hour, None, 1, round(ultimo, 2), "Limite 90%", "Som a 90% do limite", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idjogo)
                )
                db.commit()
                print(f"[MQTT->MySQL] Registro inserido na tabela mensagens: Som a 90% do limite (ID {id_sound})")
            except Exception as e:
                print(f"[MQTT->MySQL] Erro ao inserir na tabela mensagens: {e}")


    elif ultimo >= S80_LIMIT_NOISE:
        print("[Mqtt -> MySQL] Variação do som a 80% do limite.")

        with db_lock:
            try:
                cursor.execute(
                    "INSERT INTO mensagens (ID, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita, IdJogo) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (id_sound, hour, None, 2, round(ultimo, 2), "Limite 80%", "Som a 80% do limite", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idjogo)
                )
                db.commit()
                print(f"[MQTT->MySQL] Registro inserido na tabela mensagens: Som a 80% do limite (ID {id_sound})")
            except Exception as e:
                print(f"[MQTT->MySQL] Erro ao inserir na tabela mensagens: {e}")
    else:
        print("[Mqtt -> MySQL] Variação do som abaixo de 80% do limite.")

# Callback para mensagens de SOUND
def process_sound_message(payload):
    try:
        dados = json.loads(payload)
        print(f"[MQTT->MySQL] Mensagem SOUND recebida: {dados}")

        id_sound = dados.get("IDSound")
        sound = float(Decimal(dados.get("Sound")))
        hour = dados.get("Hour")

        idjogo = get_idjogo_atual()
        if idjogo is None:
            print("[MQTT->MySQL] Nenhum jogo com estado 'running' encontrado.")
            idjogo = 1

        if verificar_outlier(sound, idjogo):
            dados_som = json.dumps(
                convert_data_for_failedCollection(dados, "5. [Mqtt->MySQL] Outlier detectado", "Sound"))
            client_mqtt.publish(GROUP_MQTT_FAILED_TOPIC, dados_som)
            print(f"[MQTT->MySQL] Mensagem inválida Sound: {dados}")

            with db_lock:
                try:
                    cursor.execute(
                        "INSERT INTO mensagens (ID, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita, IdJogo) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (id_sound, hour, None , 1 , round(float(sound),2), "Outlier", "Outlier detetado", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idjogo)
                    )
                    db.commit()
                    print(f"[MQTT->MySQL] Registro inserido na tabela mensagens para outlier: ID {id_sound}")
                except Exception as e:
                    print(f"[MQTT->MySQL] Erro ao inserir na tabela mensagens: {e}")

        else:
            verificar_variacao_som(sound , id_sound, hour, idjogo)
            with db_lock:
                try:
                    cursor.execute(
                        "INSERT INTO sound (IDSound, Sound, IdJogo, Hour) VALUES (%s, %s, %s, %s)",
                        (id_sound, sound, idjogo, hour)
                    )
                    db.commit()
                    print(f"[MQTT->MySQL] Guardado no MySQL (SOUND): {dados}")
                except Exception as insert_err:
                    if "Duplicate entry" in str(insert_err):
                        print(f"[MQTT->MySQL] Som duplicado: {id_sound}")
                    else:
                        print(f"[MQTT->MySQL] Erro ao inserir som: {insert_err}")
                        return

        # Enviar ACK
        ack_message = json.dumps({
            "IDMongo": id_sound,
            "collection": "Sound"
        })
        client_mqtt.publish(GROUP_MQTT_ACK_TOPIC, ack_message, qos=2)
        print(f"[MQTT->MySQL] ACK enviado para {id_sound}")

    except Exception as e:
        print(f"[SOUND] Erro no processamento: {e}")

# Callback para mensagens de MEDIÇÕES
def process_move_message(payload):
    try:
        dados = json.loads(payload)
        print(f"[MQTT->MySQL] Mensagem MOVE recebida: {dados}")

        id_move = dados.get("IDMove")
        marsami = dados.get("Marsami")
        room_origin = dados.get("RoomOrigin")
        room_destiny = dados.get("RoomDestiny")
        status = dados.get("Status")
        hour = dados.get("Hora")

        idjogo = get_idjogo_atual()
        if idjogo is None:
            print("[MQTT->MySQL] Nenhum jogo com estado 'running' encontrado.")
            return

        if not validar_mensagem_move(dados):
            dados_move = json.dumps(convert_data_for_failedCollection(dados, "4. Mensagem inválida", "Move"))
            client_mqtt.publish(GROUP_MQTT_FAILED_TOPIC, dados_move)
            print(f"[MQTT->MySQL] Mensagem inválida Move: {dados}")
            return

        with db_lock:
            try:
                cursor.execute(
                    "INSERT INTO medicoespassagens (IDMedicao, Hora, SalaOrigem, SalaDestino, Marsami, Status, IDJogo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (id_move, hour, room_origin, room_destiny, marsami, status, idjogo)
                )
                db.commit()
                print(f"[MQTT->MySQL] Guardado no MySQL (MOVE): {dados}")
            except Exception as insert_err:
                if "Duplicate entry" in str(insert_err):
                    print(f"[MQTT->MySQL] Medição duplicada: {id_move}")
                else:
                    print(f"[MQTT->MySQL] Erro ao inserir movimento: {insert_err}")
                    return

        # Enviar ACK
        ack_message = json.dumps({
            "IDMongo": id_move,
            "collection": "Move"
        })
        client_mqtt.publish(GROUP_MQTT_ACK_TOPIC, ack_message, qos=2)
        print(f"[MQTT->MySQL] ACK enviado para {id_move}")

    except Exception as e:
        print(f"[MOVE] Erro no processamento: {e}")

# Callback MQTT unificado
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        message_queue.put((msg.topic, payload))
        print(f"[MQTT] Mensagem recebida no tópico {msg.topic}")
    except Exception as e:
        print(f"[MQTT] Erro no callback geral: {e}")

current_game_lock = threading.Lock()



# Consumidor da fila
def queue_consumer():
    while True:
        try:
            topic, payload = message_queue.get()
            if topic == GROUP_MQTT_SOUND_TOPIC:
                executor.submit(process_sound_message, payload)
            elif topic == GROUP_MQTT_MOVE_TOPIC:
                executor.submit(process_move_message, payload)
            message_queue.task_done()
        except Exception as e:
            print(f"[Consumer] Erro no consumer: {e}")
        time.sleep(0.01)

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



# New lock specifically for database operations
db_lock = threading.Lock()

def get_idjogo_atual():
    with db_lock:
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
    print("Conectado ao MQTT "+ MQTT_BROKER)
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

# Configuração do cliente MQTT
def start_mqtt_client():
    global client_mqtt
    client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client_mqtt.on_message = on_message
    client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
    client_mqtt.subscribe([
        (GROUP_MQTT_SOUND_TOPIC, 2),
        (GROUP_MQTT_MOVE_TOPIC, 2)
    ])
    print("[MQTT] Conectado e inscrito em todos os tópicos")
    client_mqtt.loop_forever()


if __name__ == "__main__":
    # Inicialização do banco de dados

    # Threads principais
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    consumer_thread = threading.Thread(target=queue_consumer, daemon=True)
    keep_alive_thread = threading.Thread(target=keep_alive_sender, daemon=True)

    mqtt_thread.start()
    consumer_thread.start()
    keep_alive_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MQTT->MySQL] Encerrando...")
        executor.shutdown(wait=True)
        db.close()
        print("[MySQL] Conexão fechada")