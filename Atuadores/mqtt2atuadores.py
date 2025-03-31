import paho.mqtt.client as mqtt
import json
import time

# Configuração do broker MQTT
MQTT_BROKER = "broker.mqttdashboard.com"  # Nome correto do broker
MQTT_PORT = 1883
MQTT_TOPIC = "pisid_mazeact"

# Criar cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Conectar ao broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Iniciar o loop em background (para evitar bloqueios)
client.loop_start()

# Função para publicar mensagens JSON no tópico MQTT
def publish_message(message):
    json_message = json.dumps(message)  # Converter para JSON
    client.publish(MQTT_TOPIC, json_message, qos=1)  # QoS = 1 para garantir entrega
    print(f"Mensagem enviada: {json_message}")

# Exemplos de mensagens a enviar
messages = [
    "{Type: Score, Player:" + str(15) +  ", Room: " + str(4) + "}" ,
    "{Type: Score, Player:" + str(15) +  ", Room: " + str(4) + "}" ,
    "{Type: Score, Player:" + str(15) +  ", Room: " + str(4) + "}" ,
    "{Type: Score, Player:" + str(15) +  ", Room: " + str(4) + "}" ,
    "{Type: Score, Player:" + str(15) +  ", Room: " + str(4) + "}" ,
    "{Type: CloseDoor, Player:" + str(15) +  ", RoomOrigin: " + str(1) + ", RoomDestiny: " + str(2) + "}",
    "{Type: CloseDoor, Player:" + str(15) +  ", RoomOrigin: " + str(1) + ", RoomDestiny: " + str(2) + "}",
    "Type: CloseDoor, Player:" + str(15) +  ", RoomOrigin: " + str(1) + ", RoomDestiny: " + str(2) + "}",
    "{Type: CloseDoor, Player:" + str(15) +  ", RoomOrigin: " + str(1) + ", RoomDestiny: " + str(2) + "}",
    "{Type: CloseDoor, Player:" + str(15) +  ", RoomOrigin: " + str(1) + ", RoomDestiny: " + str(2) + "}",
]

# Publicar cada mensagem com um pequeno intervalo
for msg in messages:
    publish_message(msg)
    time.sleep(1)  # Pequeno atraso para evitar sobrecarga no broker

# Encerrar a conexão MQTT após um tempo
time.sleep(2)
client.loop_stop()
client.disconnect()
print("Conexão encerrada.")
