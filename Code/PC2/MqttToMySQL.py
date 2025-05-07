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

# Configurações e inicializações de banco de dados
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
executor = ThreadPoolExecutor(max_workers=4)

# Evento para sinalizar parada das threads
stop_event = threading.Event()

# Função para validar datas
def validar_data(data):
    try:
        datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        print(f"[MQTT->MySQL] Data inválida: {data}.")
        return False

    datetime_obj = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
    data_atual = datetime.now()
    threshold = timedelta(minutes=DATETIME_THRESHOLD)
    if datetime_obj < data_atual - threshold or datetime_obj > data_atual + threshold:
        print(f"[MQTT->MySQL] Data fora do intervalo: {data}.")
        return False
    return True

# Função para validar mensagens de movimento
def validar_mensagem_move(doc):
    origem = doc.get("RoomOrigin")
    destino = doc.get("RoomDestiny")
    status = doc.get("Status")
    Hora = doc.get("Hora")

    if (origem == sala_min or sala_min < destino <= sala_max) and status == status_ok:
        return True
    if (origem == sala_min or destino == sala_min) and status in [status_fail, status_cansado]:
        return True
    if (sala_min < origem <= sala_max or sala_min < destino <= sala_max) and status == status_ok:
        return True
    # if not validar_data(Hora):
    #     return False
    return False

# Função para verificar outliers
def verificar_outlier(sound_value, idjogo):
    limite = NOISEVARTOL * LIMITE_DESVIO_PADRAO
    cursor.execute("SELECT Sound FROM sound WHERE IdJogo = %s ORDER BY Hour DESC LIMIT 20", (idjogo,))
    resultados = cursor.fetchall()
    historico = []

    for row in resultados:
        valor = float(row[0])
        if len(historico) >= QTD_VALS_SOUND_MAX:
            break
        if len(historico) >= QTD_VALS_SOUND_MIN:
            media = statistics.mean(historico)
            if abs(valor - media) > limite:
                continue
        historico.append(valor)

    if len(historico) < QTD_VALS_SOUND_MIN:
        return False
    media = statistics.mean(historico)
    return abs(sound_value - media) > limite

# Função para verificar variação de som
def verificar_variacao_som(sound_value, id_sound, hour, idjogo):
    VARTOL_80 = NOISEVARTOL * LIMITE_80
    VARTOL_90 = NOISEVARTOL * LIMITE_90
    S80_LIMIT_NOISE = NORMALNOISE + VARTOL_80
    S90_LIMIT_NOISE = NORMALNOISE + VARTOL_90

    try:
        ultimo = float(Decimal(sound_value))
    except (ValueError, TypeError, Decimal.InvalidOperation) as e:
        print(f"[Mqtt -> MySQL] Erro ao converter valores de som: {e}")
        return

    if ultimo >= S90_LIMIT_NOISE:
        print("[Mqtt -> MySQL] Variação do som a 90% do limite.")
        with db_lock:
            cursor.execute(
                "INSERT INTO mensagens (ID, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita, IdJogo) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (id_sound, hour, None, 1, round(ultimo, 2), "Limite 90%", "Som a 90% do limite", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idjogo)
            )
            db.commit()
    elif ultimo >= S80_LIMIT_NOISE:
        print("[Mqtt -> MySQL] Variação do som a 80% do limite.")
        with db_lock:
            cursor.execute(
                "INSERT INTO mensagens (ID, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita, IdJogo) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (id_sound, hour, None, 2, round(ultimo, 2), "Limite 80%", "Som a 80% do limite", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idjogo)
            )
            db.commit()

# Processamento de mensagens de som
def process_sound_message(payload):
    try:
        dados = json.loads(payload)
        id_sound = dados.get("IDSound")
        sound = float(Decimal(dados.get("Sound")))
        hour = dados.get("Hour")
        idjogo = get_idjogo_atual() or 1

        if verificar_outlier(sound, idjogo):
            dados_som = json.dumps(convert_data_for_failedCollection(dados, "5. [Mqtt->MySQL] Outlier detectado", "Sound"))
            client_mqtt.publish(GROUP_MQTT_FAILED_TOPIC, dados_som)
            with db_lock:
                cursor.execute(
                    "INSERT INTO mensagens (ID, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita, IdJogo) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (id_sound, hour, None, 1, round(float(sound), 2), "Outlier", "Outlier detetado", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idjogo)
                )
                db.commit()
        else:
            verificar_variacao_som(sound, id_sound, hour, idjogo)
            with db_lock:
                cursor.execute(
                    "INSERT INTO sound (IDSound, Sound, IdJogo, Hour) VALUES (%s, %s, %s, %s)",
                    (id_sound, sound, idjogo, hour)
                )
                db.commit()

        ack_message = json.dumps({"IDMongo": id_sound, "collection": "Sound"})
        client_mqtt.publish(GROUP_MQTT_ACK_TOPIC, ack_message, qos=2)
    except Exception as e:
        print(f"[SOUND] Erro no processamento: {e}")

# Processamento de mensagens de movimento
def process_move_message(payload):
    try:
        dados = json.loads(payload)
        id_move = dados.get("IDMove")
        marsami = dados.get("Marsami")
        room_origin = dados.get("RoomOrigin")
        room_destiny = dados.get("RoomDestiny")
        status = dados.get("Status")
        hour = dados.get("Hora")
        idjogo = get_idjogo_atual()
        if idjogo is None:
            return

        if not validar_mensagem_move(dados):
            dados_move = json.dumps(convert_data_for_failedCollection(dados, "4. Mensagem inválida", "Move"))
            client_mqtt.publish(GROUP_MQTT_FAILED_TOPIC, dados_move)
            return

        with db_lock:
            cursor.execute(
                "INSERT INTO medicoespassagens (IDMedicao, Hora, SalaOrigem, SalaDestino, Marsami, Status, IDJogo) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (id_move, hour, room_origin, room_destiny, marsami, status, idjogo)
            )
            db.commit()

        ack_message = json.dumps({"IDMongo": id_move, "collection": "Move"})
        client_mqtt.publish(GROUP_MQTT_ACK_TOPIC, ack_message, qos=2)
    except Exception as e:
        print(f"[MOVE] Erro no processamento: {e}")

# Callback MQTT
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        message_queue.put((msg.topic, payload))
    except Exception as e:
        print(f"[MQTT] Erro no callback geral: {e}")

# Consumidor da fila
def queue_consumer(stop_event):
    while not stop_event.is_set() or not message_queue.empty():
        try:
            topic, payload = message_queue.get(timeout=1)
            if topic == GROUP_MQTT_SOUND_TOPIC:
                executor.submit(process_sound_message, payload)
            elif topic == GROUP_MQTT_MOVE_TOPIC:
                executor.submit(process_move_message, payload)
            message_queue.task_done()
        except Queue.Empty:
            continue
        except Exception as e:
            print(f"[Consumer] Erro no consumer: {e}")

# Criação de jogo
def createGame(idjogo):
    global current_game
    with current_game_lock:
        if idjogo != current_game:
            current_game = idjogo
            cursor.execute("INSERT INTO jogo (IDJogo) VALUES (%s)", (idjogo,))
            db.commit()

# Obter ID do jogo atual
def get_idjogo_atual():
    with db_lock:
        try:
            cursor.execute("SELECT IDJogo FROM jogo WHERE Estado = 'running' ORDER BY IDJogo DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"[MQTT->MySQL] Erro ao obter IDJogo atual: {e}")
            return None

# Envio de mensagens keep-alive
def keep_alive_sender(stop_event):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("Conectado ao MQTT " + MQTT_BROKER)

    while not stop_event.is_set():
        try:
            db.ping()
            keep_alive_message = json.dumps({"status": "alive", "timestamp": datetime.now().isoformat()})
            client.publish("keep_alive", keep_alive_message)
            print("[MQTT->MySQL] Mensagem Keep Alive enviada.")
        except mariadb.Error as e:
            print(f"[MQTT->MySQL] Ligação à base de dados perdida: {e}")
            reconnect_db()
        for _ in range(20):
            if stop_event.is_set():
                break
            time.sleep(0.1)

    client.loop_stop()
    client.disconnect()
    print("[MQTT->MySQL] Keep Alive thread terminada.")

# Reconexão ao banco de dados
def reconnect_db():
    global db, cursor
    try:
        db.close()
    except:
        pass
    connected = False
    while not connected:
        try:
            db = mariadb.connect(host="127.0.0.1", user="root", password="", database="pisid_sql")
            cursor = db.cursor()
            connected = True
            print("[MQTT->MySQL] Reconectado com sucesso ao MySQL.")
        except mariadb.Error as e:
            print(f"[MQTT->MySQL] Erro ao reconectar ao MySQL: {e}")
            time.sleep(10)

# Configuração do cliente MQTT
def start_mqtt_client(stop_event):
    global client_mqtt
    try:
        client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client_mqtt.on_message = on_message
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        client_mqtt.subscribe([(GROUP_MQTT_SOUND_TOPIC, 2), (GROUP_MQTT_MOVE_TOPIC, 2)])
        print("[MQTT] Conectado e inscrito em todos os tópicos")
        client_mqtt.loop_start()
        while not stop_event.is_set():
            time.sleep(1)
        client_mqtt.loop_stop()
        client_mqtt.disconnect()
        print("[MQTT] Cliente MQTT desconectado.")
    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao iniciar cliente MQTT: {e}")
        os._exit(1)

if __name__ == "__main__":
    # Threads principais
    mqtt_thread = threading.Thread(target=start_mqtt_client, args=(stop_event,))
    consumer_thread = threading.Thread(target=queue_consumer, args=(stop_event,))
    keep_alive_thread = threading.Thread(target=keep_alive_sender, args=(stop_event,))

    mqtt_thread.start()
    consumer_thread.start()
    keep_alive_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MQTT->MySQL] Encerrando...")
        stop_event.set()
        mqtt_thread.join()
        consumer_thread.join()
        keep_alive_thread.join()
        executor.shutdown(wait=True)
        db.close()
        print("[MySQL] Conexão fechada")