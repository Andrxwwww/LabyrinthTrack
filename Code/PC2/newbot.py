import time
import mariadb
import threading
import paho.mqtt.client as mqtt

# Configurações
MQTT_BROKER = "20.39.241.21"
MQTT_TOPIC = "pisid_mazeact"
PLAYER_ID = 15
IMBALANCE_THRESHOLD = 1  # Reduzido para permitir mais movimento
CHECK_INTERVAL = 0.1   # Aumentado para evitar sobrecarga

import MySQLToMySQL
MySQLToMySQL.main()

# Estruturas de estado
door_states = {}  # {(origin, destiny): is_open}
trigger_count = {}  # {room_id: count}

# Cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# ================================================
# Funções do Banco de Dados e Inicialização
# ================================================
def get_db_connection():
    return mariadb.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="pisid_sql"
    )

def initialize_door_states():
    """Carrega conexões do banco e inicializa todas como abertas"""
    global door_states
    try:
        db = get_db_connection()
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
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT Sala, NumeroMarsamisOdd, NumeroMarsamisEven FROM ocupacaolabirinto WHERE Sala >= 1")
        rooms = cursor.fetchall()
        cursor.close()
        db.close()
        return {room["Sala"]: {"odd": room["NumeroMarsamisOdd"], "even": room["NumeroMarsamisEven"]} for room in rooms}
    except Exception as e:
        print(f"Erro ao buscar estados das salas: {e}")
        return {}

# ================================================
# Lógica de Controle de Portas
# ================================================
def calculate_imbalance(odd, even):
    return odd - even

def control_individual_doors():
    while True:
        try:
            room_states = get_room_states()
            for room_id, state in room_states.items():
                odd = state["odd"]
                even = state["even"]
                imbalance = calculate_imbalance(odd, even)
                total_marsamis = odd + even
                available_connections = [(dest, is_open) for (orig, dest), is_open in door_states.items() if orig == room_id]

                # Limite dinâmico para salas pequenas
                dynamic_threshold = max(1, total_marsamis +3 // 4)

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

# ================================================
# Lógica de Pontuação (Gatilho de Score)
# ================================================
def check_score_triggers():
    """Thread para verificar condições de pontuação"""
    while True:
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
                            print(f"⚠️ Sala {room_id} atingiu o limite de 3 triggers!")

            time.sleep(2)  # Verificar a cada 5 segundos
        except Exception as e:
            print(f"Erro na verificação de pontuação: {e}")

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
    door_thread = threading.Thread(target=control_individual_doors, daemon=True)
    score_thread = threading.Thread(target=check_score_triggers, daemon=True)
    door_thread.start()
    score_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🔴 Encerrando sistema...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()