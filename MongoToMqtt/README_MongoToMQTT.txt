1. Porquê 2 threads e não 3 ou mais threads ? Bem como o uso de uma Queue antes de escrever para o MQTT ?

- Chegámos a medir o tempo para quando se usa 3 threads (2 para cada topico escrever na queue e 1 para escrever da queue para MQTT) 
e obteu-se os seguintes resultados [3 Threads]:

> Tempo para enviar dados: 0.2662 segundos
> Tempo para enviar dados: 0.3423 segundos
> Tempo para enviar dados: 0.3843 segundos

- enquanto que para [2 Threads] foram os seguintes:

> Tempo para enviar dados: 0.0570 segundos
> Tempo para enviar dados: 0.0469 segundos
> Tempo para enviar dados: 0.0543 segundos

Com isto decidimos ficar com simplesmente 2 threads visto que a diferença de tempo acabava por ser bastante notável
PS: fizemos o mesmo da Cloud->Mongo , mas os valores de 3 para 4 threads eram bastante idênticos mas decidimos as 4 threads 
devido aos motivos descritos do 1. do README_CloudMongo.txt 