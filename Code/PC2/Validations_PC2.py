import statistics
from BDConfigs import *
import pymysql

# Obter uma constante (config) a partir do MySQL
def get_config(chave):
    cursor.execute("SELECT valor FROM configs WHERE chave = %s", (chave,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        raise ValueError(f"[MQTT->MySQL] Configuração '{chave}' não encontrada.")
    
def get_config_prof(chave):
    # Construir a consulta dinamicamente, validando a chave
    query = f"SELECT {chave} FROM setupmaze"
    
    try:
        # Executar a consulta
        cursor.execute(query)
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado[0]
        else:
            raise ValueError(f"[MQTT->MySQL] Configuração '{chave}' não encontrada.")
    
    except pymysql.connector.Error as e:
        raise ValueError(f"Erro ao acessar a base de dados: {e}")
    except Exception as e:
        raise ValueError(f"Erro inesperado: {e}")

desvio_padrao = float(get_config_prof("noisevartoleration"))
LIMITE_DESVIO_PADRAO = float(get_config("limite_desvio_padrao"))
QTD_VALS_SOUND_MAX = int(get_config("qtd_valores_sound_max"))
QTD_VALS_SOUND_MIN = int(get_config("qtd_valores_sound_mIN"))

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

# Funcao para verificar se é outlier ou nao

def verificar_outlier(doc , idjogo):

    sound_value = doc.get("Sound")

    limite = desvio_padrao * LIMITE_DESVIO_PADRAO  # Limite para considerar um valor como outlier

    # Obter os últimos 4 valores válidos do som para o jogo
    cursor.execute("""
        SELECT Sound FROM sound 
        WHERE IdJogo = %s 
        ORDER BY Hour DESC 
        LIMIT 20
    """, (idjogo,))

    resultados = cursor.fetchall()
    historico = []

    for row in resultados:
        valor = float(row[0])
        if len(historico) >= QTD_VALS_SOUND_MAX:
            break
        if len(historico) >= QTD_VALS_SOUND_MIN:
            media = statistics.mean(historico)
            if abs(valor - media) > limite:
                continue  # Ignora valores que seriam outliers
        historico.append(valor)

    if len(historico) < QTD_VALS_SOUND_MIN:
        # Se só temos 1 ou nenhum valor válido, não é possível comparar com confiança
        return False

    media = statistics.mean(historico)
    return abs(sound_value - media) > limite