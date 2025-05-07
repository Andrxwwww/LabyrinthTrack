@echo off
echo Iniciando script Python...

REM Ativar ambiente virtual, se aplicável
REM call ".\venv\Scripts\activate.bat"

REM Abrir uma nova janela apenas para o script
start "" cmd /k python MqttToMySQL.py

REM Fechar a janela do .bat imediatamente
exit