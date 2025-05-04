import paho.mqtt.client as mqtt

# Configurações fixas para o Score
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC = "pisid_mazeact" # Corrigido o nome do tópico
PLAYER_ID = 15
ROOM_ID = 2


def on_connect(client, userdata, flags, rc, properties=None):
    print("Conectado ao Broker com código:", rc)


def send_score():
    # Construir mensagem no formato específico
    mensagem = f"{{Type: Score, Player: {PLAYER_ID}, Room: {ROOM_ID}}}"

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()
        client.publish(TOPIC, mensagem, qos=2)
        print(f"Mensagem enviada: {mensagem}")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    send_score()