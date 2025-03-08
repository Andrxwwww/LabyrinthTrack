#Use the CloudToMongo.py

I. Install the paho-mqtt & Verify the installation

> pip install paho-mqtt
> pip show paho-mqtt

II. Install the pymongo & Verify

> pip install pymongo
> pip show pymongo

III. Ir para a script CloudToMongo.py e dar Run

IV. Na cmd correr:
> game 15
// ou entao outro broker para o IDJogo nao ficar todo cagado
> game 15 2 1 broker.hivemq.com 1883

#NOTAS:
- Porquê é que foi usado 3 / 4 threads ? e não 2 ou 5 ?
Cada thread tem um propósito específico no sistema neste caso estes aqui:

mqtt_thread_move -> Subscreve ao tópico de movimentos e processa mensagens MQTT
mqtt_thread_sound -> Subscreve ao tópico de sons e processa mensagens MQTT
mongo_thread -> Lê mensagens da fila (queue.Queue) e insere no MongoDB
[esta nao é necessária] check_thread -> Monitora a quantidade de mensagens recebidas e inseridas no banco de dados

Se p.ex fosse 2 Threads como 1 para ambos os topicos mqtt e outra para inserir os dados no mongo , o processamento das mensagens mqtt podia atrasar o armazenamento no MongoDB
Com + threads apenas trazia + complexidade sem grande benefícios

- Porquê é nao foi usado p.ex 2 mains e 1 .bat file para correr ambos os topicos ?
Acaba por ser uma escolha , como vantagens: seria p.ex se um dos processos travar o outro continuava a funcionar 
desvantagens: seria mais complicado a sincronizacao de informacoes sobre quantas informacoes foram recebidas

- Porquê o uso de uma Thread para Queue ? e não p.ex cada Thread escrever diretamente no Mongo ?
Como se trata de um grande volume de mensagens acaba por ser mais seguro haver um "buffer" ,[vanategns] este consegue evitar a concorrência ao acesso da base de dados 
, melhorar o desempenho e reduzir a carga para o mongoDB [várias operações de escrita]