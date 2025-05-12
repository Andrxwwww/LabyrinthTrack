import subprocess
import sys
import os
import threading
import time
def run_bot():
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "PC2"))
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

    bot_path = os.path.join(module_path, "Bot2.py")
    with open(bot_path) as f:
        code = f.read()
        exec(code, globals())

def run_mazerun():
    target_dir = "C:\\versao2"
    command = "mazerun 15 1 5 20.39.241.21 1883"
    subprocess.run(command, cwd=target_dir, shell=True)

if __name__ == "__main__":

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    time.sleep(10)
    
    mazerun_thread = threading.Thread(target=run_mazerun)
    mazerun_thread.start()

    bot_thread.join()
    mazerun_thread.join()
