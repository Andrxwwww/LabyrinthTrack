@echo off
echo Iniciando scripts Python...

REM Ativar ambiente virtual, se aplicável
REM call ".\venv\Scripts\activate.bat"

REM Iniciar os scripts em janelas separadas
start cmd /k python newMongoToMqtt.py
start cmd /k python newCloudToMongo.py

echo Scripts iniciados.
pause