import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from getpass import getpass

def on_connectMqttTemp(client, userdata, flags, rc, properties):
    print("MQTT Maze Connected with result code "+str(rc))

broker = 'broker.mqttdashboard.com'
portbroker = 1883
topic = "pisid_mazeact"

# Usar a versão mais recente da API
clientMqttMovements = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
clientMqttMovements.on_connect = on_connectMqttTemp
clientMqttMovements.connect(broker, portbroker)

try:
    mensagem = "{Type: OpenAllDoor, Player: 15}"
    clientMqttMovements.publish(topic, mensagem, qos=2)
    clientMqttMovements.loop()

except Exception as e:
    print(f"Error sendMqtt: {e}")
    pass
