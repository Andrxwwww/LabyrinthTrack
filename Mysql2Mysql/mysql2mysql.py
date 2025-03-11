import pymysql
import mariadb
from contextlib import closing


# Função para buscar dados da base de dados na nuvem
def fetch_data_from_cloud(table):
    try:
        # Usando context manager para garantir o fechamento da conexão
        with closing(pymysql.connect(
                host="194.210.86.10",
                user="aluno",
                password="aluno",
                database="maze",
                cursorclass=pymysql.cursors.DictCursor
        )) as cloud_conn:
            with closing(cloud_conn.cursor()) as cloud_cursor:
                cloud_cursor.execute(f"SELECT * FROM {table}")
                return cloud_cursor.fetchall()
    except Exception as e:
        print(f"Erro ao conectar à base de dados na nuvem: {e}")
        return None


# Função para inserir dados na base de dados local (MariaDB)
def insert_data_to_local(table, data):
    if not data:
        print(f"Nenhum dado novo para sincronizar na tabela {table}.")
        return

    try:
        conn = mariadb.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="pisis"
        )
        cursor = conn.cursor()

        if table == "Corridor":
            insert_query = """
            INSERT INTO Corridor (Rooma, Roomb, Distance, ID)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE Distance = VALUES(Distance), ID = VALUES(ID)
            """
            values = [(row['Rooma'], row['Roomb'], row['Distance'], row['ID']) for row in data]
        elif table == "SetupMaze":
            insert_query = """
            INSERT INTO SetupMaze (normalnoise, numberrooms, numbermarsamis, numberplayers, frozentime, delaytime, timemarsamilive, noisevartoleration, step, minutesstep)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                normalnoise = VALUES(normalnoise),
                numberrooms = VALUES(numberrooms),
                numbermarsamis = VALUES(numbermarsamis),
                numberplayers = VALUES(numberplayers),
                frozentime = VALUES(frozentime),
                delaytime = VALUES(delaytime),
                timemarsamilive = VALUES(timemarsamilive),
                noisevartoleration = VALUES(noisevartoleration),
                step = VALUES(step),
                minutesstep = VALUES(minutesstep)
            """
            values = [
                (
                    row['normalnoise'], row['numberrooms'], row['numbermarsamis'], row['numberplayers'],
                    row['frozentime'], row['delaytime'], row['timemarsamilive'], row['noisevartoleration'],
                    row['step'], row.get('minutesstep')
                )
                for row in data
            ]

        cursor.executemany(insert_query, values)
        conn.commit()
        print(f"{len(data)} registros sincronizados para {table}.")

    except Exception as e:
        print(f"Erro ao conectar à base de dados local: {e}")
    finally:
        cursor.close()
        conn.close()


# Sincronização das tabelas
for table in ["Corridor", "SetupMaze"]:
    data = fetch_data_from_cloud(table)
    insert_data_to_local(table, data)
