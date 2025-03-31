import paho.mqtt.client as mqtt
import json

# Configuração do broker MQTT
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "pisid_mazeact"

# Callback quando recebe uma mensagem
def on_message(client, userdata, msg):
    try:

        decoded_message = msg.payload.decode("utf-8")
        resp = decoded_message.split(", ")[0].split(": ")[1]
        print(decoded_message)
        print(resp)
        sql = "null"
        Player = decoded_message.split(", ")[1].split(":")[1]
        print(Player)
        if (resp == "CloseDoor"):
            # print("CloseDoor")
            RoomOrigem = decoded_message.split(", ")[2].split(": ")[1]
            RoomDestino = decoded_message.split(", ")[3].split(": ")[1]
            RoomDestino = RoomDestino[:len(RoomDestino) - 1]
            sql = "update corridorplayer" + str(
                Player).strip() + " set status = 0 WHERE status = 1 and player = " + str(
                Player).strip() + " and RoomA = " + str(RoomOrigem).strip() + " and RoomB = " + str(
                RoomDestino).strip() + " ;"
            print(sql)
        if (resp == "CloseAllDoor"):
            # print("CloseAllDoor")
            Player = Player[:len(Player) - 1]
            sql = "update corridorplayer" + str(
                Player).strip() + " set status = 0 WHERE status = 1 and player = " + str(Player) + ";"
            print(sql)
        if (resp == "OpenDoor"):
            # print("OpenDoor")
            RoomOrigem = decoded_message.split(", ")[2].split(": ")[1]
            RoomDestino = decoded_message.split(", ")[3].split(": ")[1]
            RoomDestino = RoomDestino[:len(RoomDestino) - 1]
            sql = "update corridorplayer" + str(
                Player).strip() + " set status = 1 WHERE status = 0 and player = " + str(
                Player).strip() + " and RoomA = " + str(RoomOrigem).strip() + " and RoomB = " + str(
                RoomDestino).strip() + " ;"
            print(sql)
        if (resp == "OpenAllDoor"):
            # print("OpenAllDoor")
            Player = Player[:len(Player) - 1]
            sql = "update corridorplayer" + str(
                Player).strip() + " set status = 1 WHERE status = 0 and player = " + str(Player).strip() + ";"
        if (resp == "CloseMaze"):
            print("CloseMaze")
            print(Player)
            Player = Player[:len(Player) - 1]
            sql = "update corridorplayer" + str(Player).strip() + " set status = -1 WHERE  player = " + str(
                Player).strip() + ";"
            print(sql)
    except json.JSONDecodeError:
        print("Erro ao decodificar a mensagem JSON")

# Criar cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Configurar callback de mensagem
client.on_message = on_message

# Conectar ao broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Subscrever ao tópico
client.subscribe(MQTT_TOPIC, qos=1)

# Iniciar o loop para escutar mensagens
print(f"A escutar mensagens no tópico '{MQTT_TOPIC}'...")
client.loop_forever()
