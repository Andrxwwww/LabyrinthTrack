import sys
import time
import mariadb
from datetime import datetime
import threading
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

# Configurações ajustadas para match com o primeiro código
MQTT_BROKER = "20.39.241.21"  # Broker do labirinto
MQTT_TOPIC = "pisid_mazeact"  # Tópico corrigido
PLAYER_ID = 15

import MySQLToMySQL
try:
    MySQLToMySQL.main()
except Exception as e:
    print(f"Erro ao executar MySQLToMySQL.main(): {e}")

# Inicialização do cliente MQTT (igual ao primeiro código)
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Erro ao configurar MQTT: {e}")
    sys.exit(1)

# Conexão com banco de dados (mantido original)
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
        sys.exit(1)


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

            time.sleep(1)

        except Exception as e:
            print(f"Erro: {e}")


#Logica para fechar todas as portas
def handle_close_all_doors():
    """
    Thread que fica verificando a tabela `mensagens` a cada 1s
    e, ao achar um alerta Limite 90% recente, fecha/abre todas
    as portas e encerra-se.
    """
    try:
        while True:
            db = get_db_connection()
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
                # converte se vier string
                if isinstance(hora_escrita, str):
                    hora = datetime.strptime(hora_escrita, "%Y-%m-%d %H:%M:%S")
                else:
                    hora = hora_escrita

                # se tiver até 10s de vida, dispara ação
                if datetime.now() - hora <= timedelta(seconds=10):
                    # 1) fecha todas as portas
                    close_msg = f'{{Type: CloseAllDoor, Player: {PLAYER_ID}}}'
                    mqtt_client.publish(MQTT_TOPIC, close_msg)
                    print(f"[CloseAllDoor] enviado em resposta ao alerta ID {msg_id}")

                    # 2) espera 5 s
                    time.sleep(10)

                    # 3) abre todas as portas
                    open_msg = f'{{Type: OpenAllDoor, Player: {PLAYER_ID}}}'
                    mqtt_client.publish(MQTT_TOPIC, open_msg)
                    print("[OpenAllDoor] enviado após 5 s")

                    break  # sai do loop e encerra a thread

            # se não achou alertas ou não são recentes, espera antes de tentar de novo
            time.sleep(0.5)

    except Exception as e:
        print(f"[CloseAllThread] Erro ao processar alerta 'Limite 90%': {e}")

# Thread mantida conforme original
if __name__ == "__main__":
    balance_thread = threading.Thread(target=check_balance)
    balance_thread.daemon = True
    balance_thread.start()

    # Se quiseres começar também a thread de CloseAll, descomenta
    close_all_thread = threading.Thread(target=handle_close_all_doors, daemon=True)
    close_all_thread.start()


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()