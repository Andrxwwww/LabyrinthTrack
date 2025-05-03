from datetime import datetime
import paho.mqtt.client as mqtt
import json
import threading
import time
from decimal import Decimal


#Coloca os valores inicias na tabela(corridor) e (setupmaze)
import MySQLToMySQL
MySQLToMySQL.main()

##coloar try cach
from BDConfigs import *
from BDdata_PC2 import *
from Bot import *

current_game = 0

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

def verificar_variacao_som(idjogo):
    limite_60 = NOISEVARTOL * LIMITE_60
    limite_80 = NOISEVARTOL * LIMITE_80

    try:
        cursor.execute("""
            SELECT Sound FROM sound 
            WHERE IdJogo = %s 
            ORDER BY Hour DESC 
            LIMIT 2
        """, (idjogo,))
        resultados = cursor.fetchall()
    except mariadb.Error as e:
        print(f"[ERRO] Erro ao aceder à base de dados: {e}")
        return

    if len(resultados) < 2:
        print("[Mqtt -> MySQL] Não há dados suficientes para verificar variação.")
        return

    try:
        ultimo = float(Decimal(resultados[0][0]))
        penultimo = float(Decimal(resultados[1][0]))
    except (ValueError, TypeError, InvalidOperation) as e:
        print(f"[Mqtt -> MySQL] Erro ao converter valores de som: {e}")
        return

    variacao = abs(ultimo - penultimo)
    print(variacao)

    if variacao >= limite_80:
        print("[Mqtt -> MySQL] Variação do som a 80% do limite.")
    elif variacao >= limite_60:
        print("[Mqtt -> MySQL] Variação do som a 60% do limite.")


# Callback para mensagens de SOUND
def on_message_sound(client, userdata, msg):
    try:

        dados = json.loads(msg.payload.decode())
        print(f"[MQTT->MySQL] Mensagem recebida: {dados}")
        id_sound = dados.get("IDSound")
        sound = float(Decimal(dados.get("Sound")))
        hour = dados.get("Hour")

        idjogo = get_idjogo_atual()
        if idjogo is None:
            print("[MQTT->MySQL] Nenhum jogo com estado 'running' encontrado.")
            idjogo=1
        
        if verificar_outlier(sound , idjogo):
            dados_som = json.dumps(convert_data_for_failedCollection(dados, "5. [Mqtt->MySQL] Outlier detectado", "Sound"))
            client.publish(GROUP_MQTT_FAILED_TOPIC, dados_som)
            print(f"[MQTT->MySQL] Mensagem inválida Sound: {dados}")
        else:
            verificar_variacao_som(idjogo)
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
                        print(f"[MQTT->MySQL] Som duplicado, já existente no MySQL: {id_sound}")
                    else:
                        print(f"[MQTT->MySQL] Erro ao inserir no MySQL: {insert_err}")
                        return  # só não envia ACK se o erro for inesperado

            # Enviar sempre o ACK
            ack_message = json.dumps({
                "IDMongo": id_sound,
                "collection": "Sound"
            })
            client.publish(GROUP_MQTT_ACK_TOPIC, ack_message, qos=2)
            print(f"[MQTT->MySQL] Enviado ACK para {id_sound}")

    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao processar mensagem SOUND: {e}")

# Callback para mensagens de MEDIÇÕES
def on_message_medicoes(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode())
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
            client.publish(GROUP_MQTT_FAILED_TOPIC, dados_move)
            print(f"[MQTT->MySQL] Mensagem inválida Move: {dados}")
            return
        else:
            with db_lock:
                try:
                    cursor.execute(
                        "INSERT INTO medicoespassagens (IDMedicao, Hora, SalaOrigem, SalaDestino, Marsami, Status, IDJogo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (id_move, hour, room_origin, room_destiny, marsami, status, idjogo)
                    )
                    db.commit()
                
                    print(f"[MQTT->MySQL] Guardado no MySQL (MEDIÇÕES): {dados}")
                except Exception as insert_err:
                    if "Duplicate entry" in str(insert_err):
                        print(f"[MQTT->MySQL] Medição duplicada, já existente no MySQL: {id_move}")
                    else:
                        print(f"[MQTT->MySQL] Erro ao inserir no MySQL: {insert_err}")
                        return  # neste caso, não envia ACK porque foi erro inesperado

        # Envia sempre o ACK, mesmo que duplicado
        ack_message = json.dumps({
            "IDMongo": id_move,
            "collection": "Move"
        })
        client.publish(GROUP_MQTT_ACK_TOPIC, ack_message, qos=2)
        print(f"[MQTT->MySQL] Enviado ACK para {id_move}")

    except Exception as e:
        print(f"[MQTT->MySQL] Erro ao processar mensagem MEDIÇÕES: {e}")


current_game_lock = threading.Lock()

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

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MQTT->MySQL] Interrompido pelo utilizador.")

    # Esperar as threads terminarem (caso seja necessário)
    thread_sound.join()
    thread_medicoes.join()
    thread_keep_alive.join()
