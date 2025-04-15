import paho.mqtt.client as mqtt
import argparse

# Função chamada ao conectar com o broker
def on_connect(client, userdata, flags, rc, properties=None):
    print("MQTT Maze Connected with result code " + str(rc))

def main():
    parser = argparse.ArgumentParser(description="Enviar mensagens MQTT para o labirinto.")
    parser.add_argument("--type", required=True, help="Tipo de ação (ex: OpenAllDoor, CloseDoor)")
    parser.add_argument("--player", type=int, default=15, help="ID do jogador (por defeito: 15)")
    parser.add_argument("--room_origin", type=int, help="Sala de origem (opcional)")
    parser.add_argument("--room_destiny", type=int, help="Sala de destino (opcional)")
    parser.add_argument("--broker", default="broker.emqx.io", help="Endereço do broker MQTT")
    parser.add_argument("--port", type=int, default=1883, help="Porta do broker MQTT")
    parser.add_argument("--topic", default="pisid_mazeact", help="Tópico MQTT")

    args = parser.parse_args()

    # Construir mensagem no formato personalizado (não JSON)
    mensagem = f"{{Type: {args.type}, Player: {args.player}"
    if args.room_origin is not None:
        mensagem += f", RoomOrigin: {args.room_origin}"
    if args.room_destiny is not None:
        mensagem += f", RoomDestiny: {args.room_destiny}"
    mensagem += "}"

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(args.broker, args.port)
    client.loop_start()

    try:
        client.publish(args.topic, mensagem, qos=2)
        print(f"Mensagem enviada: {mensagem}")
    except Exception as e:
        print(f"Erro ao enviar mensagem MQTT: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
