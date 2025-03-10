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
1. Porquê é que foi usado  3 threads ? e não 2 ou 4 ?
Cada thread tem um propósito específico no sistema neste caso estes aqui:

mqtt_thread_move -> Subscreve ao tópico de movimentos e processa mensagens MQTT e escreve para o topico pisid_mazemov_15
mqtt_thread_sound -> Subscreve ao tópico de sons e processa mensagens MQTT e escreve para o topic pisid_mazesound_15
new_game_thread -> Vai verificando quando é que é um jogo novo
[esta nao é necessária] check_thread -> Monitora a quantidade de mensagens recebidas e inseridas no banco de dados

Se fosse usada 2 threads , uma delas teria de lidar tanto com o Moves como com o Sound o que poderia atrasar o processamento de mensagens , 
4 threads tinhamos usado para 1 para queue só que não era necessário.

2. Porquê é nao foi usado p.ex 2 mains e 1 .bat file para correr ambos os topicos ?
Acaba por ser uma escolha , como vantagens: seria p.ex se um dos processos travar o outro continuava a funcionar 
desvantagens: seria mais complicado a sincronizacao de informacoes sobre quantas informacoes foram recebidas

3. Porquê não o uso de uma Thread para Queue ? e porque cada Thread escrever diretamente para o MongoDB?
Nós originalmente tinhamos chegado a fazer +1 thread para passar as mensagens para o MongoDB mas acabava por trazer algumas desvantagens como 
o aumento da latência ao passar os dados por um "buffer" para o MongoDB e também porque o MongoDB acaba por lidar com múltiplas conexões concorrentes

#Extras:

4. Contar o nº de marsamis no MongoDB , chegou-se a utilizar a .distinct(). Porque é que nao se usou o aggregation ?

- apesar do .distinct() ser mais eficiente e simples , implicava dar load de todos os dados unicos para a memoria em client-side 
que consequentemente trazia alta memory usage e slow performance, mas visto que se trata de 30 marsamis iremos considerar esta solução ,
visto que nao se trata de um large dataset

- em relação à aggregation acaba por ser processado em server-side (mongoDB) onde depois retorna so o resultado final o que acaba por ser mais eficiente
quando são large datasets maiores