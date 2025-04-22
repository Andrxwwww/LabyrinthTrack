from BDConfigs import *


# Obter uma constante (config) a partir do MySQL
def get_config(chave):
    cursor.execute("SELECT valor FROM configs WHERE chave = %s", (chave,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        raise ValueError(f"[MQTT->MySQL] Configuração '{chave}' não encontrada.")

# Função para validar mensagens de movimento
# TODO: Falta o MongoToMQTT receber as mensagens que estão nesse topico
def validar_mensagem_move(doc):

    status_ok = int(get_config("status_tudoOK"))
    status_fail = int(get_config("status_nenhuma_porta"))
    status_cansado = int(get_config("status_cansado"))
    sala_min = int(get_config("num_sala_min"))
    sala_max = int(get_config("num_sala_max"))

    origem = doc.get("RoomOrigin")
    destino = doc.get("RoomDestiny")
    status = doc.get("Status")

    # Validação 4: Sala origem igual ao mínimo e destino dentro do intervalo, status OK
    if (origem == sala_min or sala_min < destino <= sala_max) and status == status_ok:
        return True
    # Validação 5: Origem e destino iguais ao mínimo, status é "nenhuma porta" ou "cansado"
    if (origem == sala_min or destino == sala_min) and status in [status_fail, status_cansado]:
        return True
    # Validação 6: Origem e destino dentro do intervalo, status OK
    if (sala_min < origem <= sala_max or sala_min < destino <= sala_max) and status == status_ok:
        return True
    
    return False