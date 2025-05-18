import sys
import time
from datetime import datetime, timedelta
import mariadb
import threading
import paho.mqtt.client as mqtt

# Configurações
MQTT_BROKER = "20.39.241.21"
MQTT_TOPIC = "pisid_mazeact"
PLAYER_ID = 15
IMBALANCE_THRESHOLD = 1  # Reduzido para permitir mais movimento
CHECK_INTERVAL = 0.1   # Aumentado para evitar sobrecarga

# Lock para acesso seguro ao banco de dados
db_lock = threading.Lock()
# Evento para sinalizar parada de todas as threads
stop_event = threading.Event()

# Estruturas de estado
door_states = {}  # {(origin, destiny): is_open}
trigger_count = {}  # {room_id: count}

import MySQLToMySQL
try:
    MySQLToMySQL.main()
except Exception as e:
    print(f"Erro ao executar MySQLToMySQL.main(): {e}")

# Cliente MQTT
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Erro ao configurar MQTT: {e}")
    sys.exit(1)

# ================================================
# Funções do Banco de Dados e Inicialização
# ================================================
def get_db_connection():
    try:
        return mariadb.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="pisid_sql"
        )
    except mariadb.Error as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None

def initialize_door_states():
    """Carrega conexões do banco e inicializa todas como abertas"""
    global door_states
    try:
        with db_lock:
            db = get_db_connection()
            if not db:
                return
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT Rooma, Roomb FROM corridor")
            connections = cursor.fetchall()
            door_states = {(conn['Rooma'], conn['Roomb']): True for conn in connections}
            print(f"Portas inicializadas: {door_states}")
            cursor.close()
            db.close()
    except Exception as e:
        print(f"Erro ao inicializar portas: {e}")


def get_room_states():
    try:
        with db_lock:
            db = get_db_connection()
            if not db:
                return {}
            cursor = db.cursor(dictionary=True)

            # Obter o IDJogo atual
            cursor.execute("SELECT IDJogo FROM jogo WHERE Estado = 'running' ORDER BY IDJogo DESC LIMIT 1")
            result = cursor.fetchone()
            if not result:
                print("Nenhum jogo em execução encontrado.")
                cursor.close()
                db.close()
                return {}
            id_jogo_atual = result['IDJogo']

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
        return {room["Sala"]: {"odd": room["NumeroMarsamisOdd"], "even": room["NumeroMarsamisEven"]} for room in rooms}
    except Exception as e:
        print(f"Erro ao buscar estados das salas: {e}")
        return {}

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

# ================================================
# Lógica de Controle de Portas
# ================================================
def calculate_imbalance(odd, even):
    return odd - even

def control_individual_doors():
    while not stop_event.is_set():
        try:
            room_states = get_room_states()
            for room_id, state in room_states.items():
                odd = state["odd"]
                even = state["even"]
                imbalance = calculate_imbalance(odd, even)
                total_marsamis = odd + even
                available_connections = [(dest, is_open) for (orig, dest), is_open in door_states.items() if orig == room_id]

                # Limite dinâmico para salas pequenas
                dynamic_threshold = max(1, total_marsamis // 4)

                if abs(imbalance) > dynamic_threshold:
                    needed_type = "even" if imbalance > 0 else "odd"
                    for adj_room, is_open in available_connections:
                        adj_state = room_states.get(adj_room, {"odd": 0, "even": 0})
                        if (needed_type == "even" and adj_state["even"] > adj_state["odd"]) or \
                           (needed_type == "odd" and adj_state["odd"] > adj_state["even"]):
                            if not is_open:
                                open_door(room_id, adj_room)
                        else:
                            if is_open:
                                close_door(room_id, adj_room)
                elif abs(imbalance) <= dynamic_threshold:
                    # Permitir ajustes finos em desequilíbrios pequenos
                    for adj_room, is_open in available_connections:
                        adj_state = room_states.get(adj_room, {"odd": 0, "even": 0})
                        if (imbalance > 0 and adj_state["even"] > adj_state["odd"]) or \
                           (imbalance < 0 and adj_state["odd"] > adj_state["even"]) or \
                           abs(imbalance) == 0:
                            if not is_open:
                                open_door(room_id, adj_room)
                        else:
                            if is_open:
                                close_door(room_id, adj_room)

            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Erro no controle de portas: {e}")
            time.sleep(CHECK_INTERVAL)

# ================================================
# Lógica de Pontuação (Gatilho de Score)
# ================================================
def check_score_triggers():
    """Thread para verificar condições de pontuação"""
    while not stop_event.is_set():
        try:
            room_states = get_room_states()
            for room_id, state in room_states.items():
                odd = state["odd"]
                even = state["even"]

                # Condições para disparar o Score
                if odd == even and (odd + even) > 2:
                    if room_id not in trigger_count:
                        trigger_count[room_id] = 0

                    if trigger_count[room_id] < 3:
                        trigger_count[room_id] += 1
                        mensagem = f'{{Type: Score, Player: {PLAYER_ID}, Room: {room_id}}}'
                        mqtt_client.publish(MQTT_TOPIC, mensagem)
                        print(f"[SCORE TRIGGER] {mensagem}")

                        if trigger_count[room_id] == 3:
                            print(f" Sala {room_id} atingiu o limite de 3 triggers!")

            time.sleep(2)  # Verificar a cada 2 segundos
        except Exception as e:
            print(f"Erro na verificação de pontuação: {e}")
            time.sleep(2)

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

# ================================================
# Funções de Controle de Portas
# ================================================
def open_door(origin, destiny):
    door_states[(origin, destiny)] = True
    mensagem = f'{{Type: OpenDoor, Player: {PLAYER_ID}, RoomOrigin: {origin}, RoomDestiny: {destiny}}}'
    mqtt_client.publish(MQTT_TOPIC, mensagem)
    print(f"[PORTA ABERTA] {origin}→{destiny}")

def close_door(origin, destiny):
    door_states[(origin, destiny)] = False
    mensagem = f'{{Type: CloseDoor, Player: {PLAYER_ID}, RoomOrigin: {origin}, RoomDestiny: {destiny}}}'
    mqtt_client.publish(MQTT_TOPIC, mensagem)
    print(f"[PORTA FECHADA] {origin}→{destiny}")

# ================================================
# Execução Principal
# ================================================
if __name__ == "__main__":
    initialize_door_states()

    # Iniciar threads
    game_status_thread = threading.Thread(target=check_game_status, daemon=True)
    door_thread = threading.Thread(target=control_individual_doors, daemon=True)
    score_thread = threading.Thread(target=check_score_triggers, daemon=True)
    close_all_thread = threading.Thread(target=handle_close_all_doors, daemon=True)

    game_status_thread.start()
    door_thread.start()
    score_thread.start()
    close_all_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
        print("\n Encerrando sistema...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n Encerrando por interrupção do usuário...")
        stop_event.set()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        sys.exit(0)