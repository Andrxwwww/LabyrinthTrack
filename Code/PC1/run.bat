@echo off
echo Iniciando scripts Python...

REM Abrir duas janelas separadas com os scripts
start "" cmd /k python oldMongoToMqtt.py
start "" cmd /k python oldCloudToMongo.py

REM Fechar imediatamente a janela do .bat
exit