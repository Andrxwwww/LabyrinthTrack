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
    # PARA SOUND
    NOISEVARTOL = float(get_config_prof("noisevartoleration"))
    NORMALNOISE = float(get_config_prof("normalnoise"))
    LIMITE_DESVIO_PADRAO = float(get_config("limite_desvio_padrao"))
    QTD_VALS_SOUND_MAX = int(get_config("qtd_valores_sound_max"))
    QTD_VALS_SOUND_MIN = int(get_config("qtd_valores_sound_mIN"))
    LIMITE_80 = float(get_config("limite_80"))
    LIMITE_90 = float(get_config("limite_90"))
    DATETIME_THRESHOLD = float(get_config("datetime_threshold"))

    # PARA MOVE
    status_ok = int(get_config("status_tudoOK"))
    status_fail = int(get_config("status_nenhuma_porta"))
    status_cansado = int(get_config("status_cansado"))
    sala_min = int(get_config("num_sala_min"))
    sala_max = int(get_config("num_sala_max"))


except Exception as e:
    print(f"Erro ao carregar configurações globais: {e}")
    print("[AVISO] A usar valores padrão de emergência.")
    NORMALNOISE = 19
    NOISEVARTOL = 2.5
    LIMITE_DESVIO_PADRAO = 3.0
    QTD_VALS_SOUND_MAX = 4
    QTD_VALS_SOUND_MIN = 2
    LIMITE_80 = 0.8
    LIMITE_90 = 0.90
    DATETIME_THRESHOLD = 5

    status_ok = 1
    status_fail = 0
    status_cansado = 2
    sala_min = 1
    sala_max = 10
    