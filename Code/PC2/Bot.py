import time
import mariadb
from datetime import datetime
import threading
import paho.mqtt.client as mqtt

# Configurações ajustadas para match com o primeiro código
MQTT_BROKER = "98.66.160.46"  # Broker do labirinto
MQTT_TOPIC = "pisid_mazeact"  # Tópico corrigido
PLAYER_ID = 15

# Inicialização do cliente MQTT (igual ao primeiro código)
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()


# Conexão com banco de dados (mantido original)
def get_db_connection():
    return mariadb.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="pisid_sql"
    )


# Função modificada para formato de mensagem correto
def check_balance():
    trigger_count = {}
    while True:
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
                odd = room["NumeroMarsamisOdd"]
                even = room["NumeroMarsamisEven"]

                if room_id not in trigger_count:
                    trigger_count[room_id] = 0

                # Lógica de trigger mantida
                if odd == even and (odd + even) > 2 and trigger_count[room_id] < 3:
                    trigger_count[room_id] += 1

                    # Mensagem formatada como string (igual ao primeiro código)
                    mensagem = f'{{Type: Score, Player: {PLAYER_ID}, Room: {room_id}}}'

                    mqtt_client.publish(MQTT_TOPIC, mensagem)
                    print(f"Publicado: {mensagem}")

                    if trigger_count[room_id] == 3:
                        print(f"Sala {room_id} atingiu 3 tentativas!")

            time.sleep(5)

        except Exception as e:
            print(f"Erro: {e}")


# Thread mantida conforme original
if __name__ == "__main__":
    balance_thread = threading.Thread(target=check_balance)
    balance_thread.daemon = True
    balance_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()