import statistics
from decimal import Decimal, InvalidOperation

from BDConfigs import *
from datetime import datetime, timedelta

# Função para converter dados para o formato de failedCollection
def convert_data_for_failedCollection(dados, report, collection):
    return {
        "IDMessage": dados.get("IDMove") or dados.get("IDSound"),
        "Collection": dados.get("Collection"),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Message": dados,
        "Report": report,
        "Collection": collection
    }

# Obter uma constante (config) a partir do MySQL
def get_config(chave):
    try:
        cursor.execute("SELECT valor FROM configs WHERE chave = %s", (chave,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        else:
            raise ValueError(f"[MQTT->MySQL] Configuração '{chave}' não encontrada.")
    except mariadb.ProgrammingError as e:
        print(f"[ERRO] Tabela configs não existe ou erro de sintaxe: {e}")
        sys.exit()
    except mariadb.Error as e:
        print(f"[ERRO] Falha na consulta: {e}")
        sys.exit()


    
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
    except Exception as e:
        print(f"[ERRO] Falha na conexão com o banco local: {e}")
        sys.exit(1)
        #todo decidir se se coloca valores padrão

try:
    NOISEVARTOL = float(get_config_prof("noisevartoleration"))
    LIMITE_DESVIO_PADRAO = float(get_config("limite_desvio_padrao"))
    QTD_VALS_SOUND_MAX = int(get_config("qtd_valores_sound_max"))
    QTD_VALS_SOUND_MIN = int(get_config("qtd_valores_sound_mIN"))
    LIMITE_60 = float(get_config("limite_60"))
    LIMITE_80 = float(get_config("limite_80"))
    DATETIME_THRESHOLD = float(get_config("datetime_threshold"))
except Exception as e:
    print(f"Erro ao carregar configurações globais: {e}")
    print("[AVISO] A usar valores padrão de emergência.")
    NOISEVARTOL = 19
    LIMITE_DESVIO_PADRAO = 3.0
    QTD_VALS_SOUND_MAX = 4
    QTD_VALS_SOUND_MIN = 2
    LIMITE_60 = 0.6
    LIMITE_80 = 0.8
    DATETIME_THRESHOLD = 5


# Função para validar datas
def validar_data(data):

    # Verifica se a data está no formato correto
    try:
        datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        print(f"[MQTT->MySQL] Data inválida: {data}.")
        return False
    
    # Validação 4: Verifica se a data está atual e no intervalo correto
    datetime_obj = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
    data_atual = datetime.now()
    threshold = timedelta(minutes=DATETIME_THRESHOLD)
    if datetime_obj < data_atual - threshold or datetime_obj > data_atual + threshold:
        print(f"[MQTT->MySQL] Data fora do intervalo: {data}.")
        return False

    return True


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
    Hora = doc.get("Hora")

    # Validação 4: Sala origem igual ao mínimo e destino dentro do intervalo, status OK
    if (origem == sala_min or sala_min < destino <= sala_max) and status == status_ok:
        return True
    
    # Validação 5: Origem e destino iguais ao mínimo, status é "nenhuma porta" ou "cansado"
    if (origem == sala_min or destino == sala_min) and status in [status_fail, status_cansado]:
        return True
    
    # Validação 6: Origem e destino dentro do intervalo, status OK
    if (sala_min < origem <= sala_max or sala_min < destino <= sala_max) and status == status_ok:
        return True
    
    # TODO: DEPOIS TIRAR PARA DADOS MAIS RECENTES
    # Validação 7: Verificar se a data está dentro do intervalo
    #if not validar_data(Hora):
    #   return False
    
    return False

# Funcao para verificar se é outlier ou nao

def verificar_outlier(sound_value , idjogo):
    
    limite = NOISEVARTOL * LIMITE_DESVIO_PADRAO  # Limite para considerar um valor como outlier

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

def verificar_variacao_som(idjogo):
    limite_60 = NOISEVARTOL * LIMITE_60
    limite_80 = NOISEVARTOL * LIMITE_80

    try:
        cursor.execute("""
            SELECT Sound FROM sound 
            WHERE IdJogo = %s 
            ORDER BY Hour DESC 
            LIMIT 2
        """, (idjogo,))
        resultados = cursor.fetchall()
    except mariadb.Error as e:
        print(f"[ERRO] Erro ao aceder à base de dados: {e}")
        return

    if len(resultados) < 2:
        print("[Mqtt -> MySQL] Não há dados suficientes para verificar variação.")
        return

    try:
        ultimo = float(Decimal(resultados[0][0]))
        penultimo = float(Decimal(resultados[1][0]))
    except (ValueError, TypeError, InvalidOperation) as e:
        print(f"[Mqtt -> MySQL] Erro ao converter valores de som: {e}")
        return

    variacao = abs(ultimo - penultimo)
    print(variacao)

    if variacao >= limite_80:
        print("[Mqtt -> MySQL] Variação do som a 80% do limite.")
    elif variacao >= limite_60:
        print("[Mqtt -> MySQL] Variação do som a 60% do limite.")