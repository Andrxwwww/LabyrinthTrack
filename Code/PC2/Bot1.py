import sys
import time
import mariadb
from datetime import datetime, timedelta
import threading
import paho.mqtt.client as mqtt

# Configurações ajustadas
MQTT_BROKER = "20.39.241.21"  # Broker do labirinto
MQTT_TOPIC = "pisid_mazeact"  # Tópico corrigido
PLAYER_ID = 15

# Lock para acesso seguro ao banco de dados
db_lock = threading.Lock()
# Evento para sinalizar parada de todas as threads
stop_event = threading.Event()

import MySQLToMySQL
try:
    MySQLToMySQL.main()
except Exception as e:
    print(f"Erro ao executar MySQLToMySQL.main(): {e}")

# Inicialização do cliente MQTT
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Erro ao configurar MQTT: {e}")
    sys.exit(1)

# Conexão com banco de dados
def get_db_connection():
    try:
        return mariadb.connect(
            host="127.0.0.1",
            user="script2",
            password="12345",
            database="pisid_sql"
        )
    except mariadb.Error as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None

# Função para verificar o ID do jogo atual
def get_idjogo_atual():
    with db_lock:
        try:
            db = get_db_connection()
            if not db:
                return None
            cursor = db.cursor()
            cursor.execute("SELECT IDJogo FROM jogo WHERE Estado = 'running' ORDER BY IDJogo DESC LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            db.close()
            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"[MQTT->MySQL] Erro ao obter IDJogo atual: {e}")
            return None

# Função para verificar estado do jogo e encerrar se não houver jogo ativo
def check_game_status():
    while not stop_event.is_set():
        if not get_idjogo_atual():
            print("Nenhum jogo em execução. Sinalizando parada do script...")
            stop_event.set()  # Sinaliza todas as threads para parar
            break
        time.sleep(1)


# Função para verificar balanceamento
def check_balance():
    trigger_count = {}
    while not stop_event.is_set():
        try:
            with db_lock:
                db = get_db_connection()
                if not db:
                    continue
                cursor = db.cursor(dictionary=True)

                # Obter o IDJogo atual usando a função existente
                id_jogo_atual = get_idjogo_atual()
                if not id_jogo_atual:
                    print("Nenhum jogo em execução encontrado.")
                    cursor.close()
                    db.close()
                    time.sleep(1)
                    continue

                # Buscar os estados das salas para o IDJogo atual
                cursor.execute(
                    "SELECT Sala, NumeroMarsamisOdd, NumeroMarsamisEven "
                    "FROM ocupacaolabirinto "
                    "WHERE Sala >= 1 AND IDJogo = %s",
                    (id_jogo_atual,)
                )
                rooms = cursor.fetchall()
                cursor.close()
                db.close()

            for room in rooms:
                room_id = room["Sala"]
                odd = room["NumeroMarsamisOdd"]
                even = room["NumeroMarsamisEven"]

                if room_id not in trigger_count:
                    trigger_count[room_id] = 0

                if odd == even and (odd + even) > 2 and trigger_count[room_id] < 3:
                    trigger_count[room_id] += 1

                    mensagem = f'{{Type: Score, Player: {PLAYER_ID}, Room: {room_id}}}'
                    mqtt_client.publish(MQTT_TOPIC, mensagem)
                    print(f"Publicado: {mensagem}")

                    if trigger_count[room_id] == 3:
                        print(f"Sala {room_id} atingiu 3 tentativas!")

            time.sleep(1)

        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(1)

# Lógica para fechar todas as portas
def handle_close_all_doors():
    try:
        while not stop_event.is_set():
            with db_lock:
                db = get_db_connection()
                if not db:
                    continue
                cursor = db.cursor()
                cursor.execute(
                    "SELECT ID, HoraEscrita "
                    "FROM mensagens "
                    "WHERE TipoAlerta = %s "
                    "ORDER BY ID DESC LIMIT 1",
                    ("Limite 80%",)
                )
                row = cursor.fetchone()
                cursor.close()
                db.close()

            if row:
                msg_id, hora_escrita = row
                if isinstance(hora_escrita, str):
                    hora = datetime.strptime(hora_escrita, "%Y-%m-%d %H:%M:%S")
                else:
                    hora = hora_escrita

                if datetime.now() - hora <= timedelta(seconds=10):
                    close_msg = f'{{Type: CloseAllDoor, Player: {PLAYER_ID}}}'
                    mqtt_client.publish(MQTT_TOPIC, close_msg)
                    print(f"[CloseAllDoor] enviado em resposta ao alerta ID {msg_id}")

                    time.sleep(10)

                    open_msg = f'{{Type: OpenAllDoor, Player: {PLAYER_ID}}}'
                    mqtt_client.publish(MQTT_TOPIC, open_msg)
                    print("[OpenAllDoor] enviado após 10 s")

                    break

            time.sleep(0.5)

    except Exception as e:
        print(f"[CloseAllThread] Erro ao processar alerta 'Limite 80%': {e}")

# Threads principais
if __name__ == "__main__":
    # Thread para verificar o estado do jogo
    game_status_thread = threading.Thread(target=check_game_status, daemon=True)
    game_status_thread.start()

    # Thread para verificar o balanceamento
    balance_thread = threading.Thread(target=check_balance, daemon=True)
    balance_thread.start()

    # Thread para fechar/abrir portas
    close_all_thread = threading.Thread(target=handle_close_all_doors, daemon=True)
    close_all_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
        print("Encerrando script...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        sys.exit(0)
    except KeyboardInterrupt:
        print("Encerrando por interrupção do usuário...")
        stop_event.set()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        sys.exit(0)