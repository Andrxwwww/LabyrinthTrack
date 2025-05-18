# PISID Labyrinth Tracking Project

This project is a distributed system for managing and monitoring a maze game, integrating web, database, MQTT, and Python automation. It is designed for academic purposes at ISCTE.

## Project Structure

```
.
├── Code/
│   ├── run.py
│   ├── PC1/
│   └── PC2/
├── Instrucoes/
│
├── MazeServers/
│
├── Php's/
│
├── Pisid_site/
│
├── SPs/
│
└── Triggers/

```

## Main Components

### 1. Python Scripts

- **[obterPontuacao.py](obterPontuacao.py)**  
  Fetches player scores from the remote ISCTE MySQL database. This is a .py test file
  Usage:
  ```sh
  python obterPontuacao.py <PlayerID>
  ```

- **Code/PC1/**  
  - `CloudToMongo.py`: Receives MQTT messages and stores them in MongoDB.
  - `MongoToMqtt.py`: Publishes data from MongoDB to MQTT topics.
  - `MongoConfigs.py`: Configuration for MQTT and MongoDB connections.
  - `run.bat`: Starts both main PC1 scripts in separate terminals.

- **Code/PC2/**  
  - `Bot2.py`: Main bot logic for controlling doors and game logic.
  - `run2.bat`: Starts the PC2 bot script and MySQL script.

### 2. PHP Web Application (`Pisid_site/`)

- **Frontend:**  
  - `index.php`: Login and registration page.
  - `dashboard.php`: Main dashboard for managing games.
  - `CriarJogo.php`, `criarJogoHandler.php`: Create new games.
  - `editar.php`, `editarJogoHandler.php`: Edit existing games.
  - `score_graph.php`: Visualizes player scores using Chart.js.
  - `style.css`, `script.js`: UI styling and interactivity.

- **Backend:**  
  - `db.php`: Database connection.
  - `register.php`, `logout.php`, `users.php`: User management.

### 3. PHP API Scripts (`Php's/`)

- **abrirPorta.php / fecharPorta.php**: Open/close individual doors via Python MQTT sender.
- **abrirTodasPortas.php / fecharTodasPortas.php**: Open/close all doors.
- **getMarsamRoom.php, getMsgs.php, getSensors.php**: Fetch maze state, messages, and sensor data.
- **iniciarJogo.php**: Starts the game by running a batch file.
- **obterPontuacao.php**: Calls `obterPontuacao.py` and returns the result as JSON.

### 4. Database

- **SPs/**: Stored procedures for game logic.
- **Triggers/**: SQL triggers for database events.
- **Instrucoes/**: Instructions and permissions for setup.

### 5. MazeServers

- **RunMazeServers.bat**: Starts three MongoDB servers for distributed storage.
- **README_RunServers.txt**: Instructions for running and maintaining the servers.

## Setup & Usage

### Requirements

- Python 3.x (`pip install mysql-connector-python`)
- PHP 7.x+
- MySQL/MariaDB and MongoDB
- MQTT Broker (configured in `MongoConfigs.py`)
- Web server (e.g., XAMPP, WAMP)

### Running the System

1. **Start MySQL:**  
   Run on XAMPP the DB on PC2

2. **Start PC1 Scripts:**  
   Run `Code/PC1/run.bat` to launch both `CloudToMongo.py` and `MongoToMqtt.py`.

3. **Start PC2 Bot:**  
   Run `Code/PC2/run2.bat` or execute `Bot2.py` and `MqttToMySQL.py` directly.

4. **Web Application:**  
   Deploy the `Pisid_site/` and `Php's/` folders to your web server.

5. **Database:**  
   Import stored procedures and triggers from `SPs/` and `Triggers/` into your MySQL/MariaDB database.

6. **Access the Dashboard:**  
   Open the web app in your browser, register/login, and manage games.

UPDATE: Probably not working anymore because it was a university project using 

## Authors

- Grupo 15, PISID, ISCTE

## License

This project is for academic use only.
