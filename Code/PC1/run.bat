@echo off
echo Iniciando scripts Python...

REM Abrir duas janelas separadas com os scripts
start "" cmd /k python MongoToMqtt.py
start "" cmd /k python CloudToMongo.py

REM Fechar imediatamente a janela do .bat
exit