from datetime import datetime
from contextlib import closing
import pymysql
from MongoConfigs import *


# Função para buscar um campo específico de uma tabela
def getValueFromTableAndColumn(table, column):
    try:
        with closing(pymysql.connect(
            host="194.210.86.10",
            user="aluno",
            password="aluno",
            database="maze",
            cursorclass=pymysql.cursors.DictCursor
        )) as cloud_conn:
            with closing(cloud_conn.cursor()) as cloud_cursor:
                query = f"SELECT `{column}` FROM `{table}` LIMIT 1"
                cloud_cursor.execute(query)
                result = cloud_cursor.fetchone()
                if result and column in result:
                    return result[column]
                else:
                    print(f"Coluna '{column}' não encontrada ou sem dados.")
                    return None
    except Exception as e:
        print(f"Erro ao conectar à base de dados na nuvem: {e}")
        return None

# Função para verificar se dois valores existem como par Rooma/Roomb
def verifyMovimentoValido(roomOrigin, roomDestiny):

    # Spawn de Marsamis e cansaço de marsamis
    if (roomOrigin == 0 and roomDestiny != 0 ) or ( roomOrigin == 0 and roomDestiny == 0 ):
        return True
    
    try:
        with closing(pymysql.connect(
            host="194.210.86.10",
            user="aluno",
            password="aluno",
            database="maze",
            cursorclass=pymysql.cursors.DictCursor
        )) as conn:
            with closing(conn.cursor()) as cursor:
                query = """
                    SELECT * FROM corridor
                    WHERE Rooma = %s AND Roomb = %s
                """
                cursor.execute(query, (roomOrigin, roomDestiny))
                resultado = cursor.fetchone()
                return resultado is not None
    except Exception as e:
        print(f"Erro ao conectar ou consultar a base de dados: {e}")
        return False

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

def checkDataDuplicated(data, collection):
    try:
        query_move = {
            "Hora": data
        }
        count_move = collection_move.count_documents(query_move)

        query_sound = {
            "Hour": data
        }
        
        count_sound = collection_sound.count_documents(query_sound)
        print(f"[VALIDAÇÃO] Contagem de datas duplicadas: Move={count_move}, Sound={count_sound}")

        if count_move + count_sound > 1:
            print(f"[VALIDAÇÃO] Data duplicada encontrada: {data}")
            return False
        
        return True
    
    except Exception as e:
        print(f"[VALIDAÇÃO] Erro ao verificar duplicidade: {e}")
        return True

# Função para validar o movimento
def validar_movimento(doc):
    try:
        marsami = int(doc.get("Marsami"))
        origem = doc.get("RoomOrigin")
        destino = doc.get("RoomDestiny")
        status = doc.get("Status")
        hora = doc.get("Hora")

        # Validação 1: Verificar se os tipos estão corretos antes de fazer a comparação
        if not isinstance(origem, int) or not isinstance(destino, int) or not isinstance(status, int) or not isinstance(marsami, int):
            print(f"[VALIDAÇÃO] Tipos incompatíveis: origem={type(origem)}, destino={type(destino)}, status={type(status)}, marsami={type(marsami)}")
            return False
        
        # Validacao 2: Verificar se os marsamis são válidos
        if marsami is None or marsami < 1 or marsami > getValueFromTableAndColumn("SetupMaze", "numbermarsamis"):
            print(f"[VALIDAÇÃO] Marsami inválido: {marsami}")
            return False
        
        # Validação 3: Varificar o formato da Hora
        try:
            datetime.strptime(hora, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            print(f"[VALIDAÇÃO] Formato de hora inválido: {hora}")
            return False
        
        # Validacao 4: Verificar se os Rooms são válidos
        if origem is None or destino is None or origem < 0 or origem > getValueFromTableAndColumn("SetupMaze", "numberrooms") or destino < 0 or destino > getValueFromTableAndColumn("SetupMaze", "numberrooms"):
            print(f"[VALIDAÇÃO] Rooms inválidos: origem={origem}, destino={destino}")
            return False
        
        # Validação 5: Verificar se o movimento é válido
        if not verifyMovimentoValido(origem, destino):
            print(f"[VALIDAÇÃO] Movimento inválido: {origem} -> {destino}")
            return False
        
        # Validação 6: Verificar se a data é duplicada
        if not checkDataDuplicated(hora, MONGO_COLLECTION_MOVE):
            print(f"[VALIDAÇÃO] Data duplicada: {hora}")
            return False
    
        return True

    except Exception as e:
        print(f"[VALIDAÇÃO] Erro ao validar documento: {e}")
        return False

# Função para validar o som
def validar_sound(doc):
    try:
        hour = doc.get("Hour")
        sound = doc.get("Sound")

        # Validação 1: Verificar se o formato de hora está correto
        try:
            # Tentar converter o formato da hora
            datetime.strptime(hour, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            print(f"[VALIDAÇÃO] Formato de hora inválido: {hour}")
            return False

        # Validação 2: Verificar se o valor de Sound é um número válido (float)
        try:
            sound_value = float(sound)  # Converte a string para float
        except ValueError:
            print(f"[VALIDAÇÃO] Valor de Sound inválido: {sound}")
            return False

        # Validação 3: Verificar se o valor de Sound é um número inteiro (se necessário)
        if not isinstance(sound_value, (int, float)):
            print(f"[VALIDAÇÃO] Tipo inválido para Sound: {type(sound_value)}")
            return False
        
        # Validacao 4: Verificar se o valor de Sound nao é negativo 
        if sound_value < 0:
            print(f"[VALIDAÇÃO] Valor de Sound negativo: {sound_value}")
            return False
        
        # Validação 5: Verificar se a data é duplicada
        if not checkDataDuplicated(hour, MONGO_COLLECTION_SOUND):
            print(f"[VALIDAÇÃO] Data duplicada: {hour}")
            return False

        return True

    except Exception as e:
        print(f"[VALIDAÇÃO] Erro ao validar documento Sound: {e}")
        return False
