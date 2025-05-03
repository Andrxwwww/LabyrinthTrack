import json
import time
import mariadb
from datetime import datetime
import threading
import paho.mqtt.client as mqtt

# MQTT setup
MQTT_BROKER = "broker.emqx.io"  # Adjust this to your MQTT broker address if needed
MQTT_TOPIC = "pisid_mazeact"
PLAYER_ID = 15

# Initialize MQTT client
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# Database connection
def get_db_connection():
    return mariadb.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="pisid_sql"
    )

# Fetch room status from database
def get_room_status(room_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT NumeroMarsamisOdd, NumeroMarsamisEven, Sala FROM ocupacaolabirinto WHERE Sala = %s",
            (room_id,)
        )
        room_data = cursor.fetchone()
        print(f"Room data fetched: {room_data}")
        cursor.close()
        db.close()
        return room_data
    except mariadb.Error as e:
        print(f"Database error: {e}")
        return None

# Track triggers per room (not per player)
trigger_count = {}  # {room_id: count}
player_points = {}

def process_move(move_data):
    move = json.loads(move_data)
    room_id = move["RoomOrigin"]
    player_id = move["Player"]
    marsami = move["Marsami"]
    
    # Initialize tracking if not exists
    if room_id not in trigger_count:
        trigger_count[room_id] = 0
    
    # Check room status
    room_status = get_room_status(room_id)
    if not room_status:
        return {"error": "Room not found"}
    
    odd_count = room_status["NumeroMarsamisOdd"]
    even_count = room_status["NumeroMarsamisEven"]
    
    # Determine if Marsami is odd or even
    is_odd = marsami % 2 == 1
    if is_odd:
        odd_count += 1
    else:
        even_count += 1
    
    # Check if trigger can be activated
    if trigger_count[room_id] < 3 and odd_count == even_count:
        trigger_count[room_id] += 1
        
        # Simulate checking if balance holds after move
        if move["Status"] == 1:  # Assuming Status 1 means move completed
            # Check if balance still holds after potential move to RoomDestiny
            dest_status = get_room_status(move["RoomDestiny"])
            if dest_status and dest_status["NumeroMarsamisOdd"] == dest_status["NumeroMarsamisEven"]:
                if player_id not in player_points:
                    player_points[player_id] = 0
                player_points[player_id] += 1
                return {"message": f"Player {player_id} gains 1 point. Total: {player_points[player_id]}", "trigger_count": trigger_count[room_id]}
            else:
                if player_id not in player_points:
                    player_points[player_id] = 0
                player_points[player_id] -= 0.5
                return {"message": f"Player {player_id} loses 0.5 points. Total: {player_points[player_id]}", "trigger_count": trigger_count[room_id]}
        else:
            return {"message": "Move not completed, no points awarded"}
    else:
        return {"message": "Trigger not allowed or balance not equal"}

def check_balance():
    while True:  # Loop infinito
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT Sala, NumeroMarsamisOdd, NumeroMarsamisEven FROM ocupacaolabirinto WHERE Sala >= 1"
            )
            rooms = cursor.fetchall()
            cursor.close()
            db.close()
            for room in rooms:
                room_id = room["Sala"]
                odd_count = room["NumeroMarsamisOdd"]
                even_count = room["NumeroMarsamisEven"]
                if room_id not in trigger_count:
                    trigger_count[room_id] = 0
                attempts = trigger_count[room_id]
                if odd_count == even_count and (odd_count + even_count) > 2 and attempts < 3:
                    trigger_count[room_id] += 1
                    attempts = trigger_count[room_id]
                    mqtt_message = {
                        "Type": "Score",
                        "Player": PLAYER_ID,
                        "Room": room_id
                    }
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(mqtt_message))
                    print(f"Publicado no tópico MQTT {MQTT_TOPIC}: {mqtt_message}")
                    if attempts == 3:
                        print(f"Sala {room_id} atingiu o máximo de 3 tentativas!")
            time.sleep(5)  # Verifica a cada 5 segundos
        except mariadb.Error as e:
            print(f"Erro no banco de dados: {e}")
        except Exception as e:
            print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    # Inicie a thread para verificar o saldo continuamente
    balance_thread = threading.Thread(target=check_balance)
    balance_thread.daemon = True  # Permite que a thread termine quando o programa principal terminar
    balance_thread.start()

    try:
        # Mantenha o programa principal em execução
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()