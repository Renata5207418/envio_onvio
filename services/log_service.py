import os
from datetime import datetime

LOG_FOLDER = 'logs'

# Cria a pasta de logs se não existir
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)


def registrar_log(mensagem):
    hoje = datetime.now().strftime("%Y-%m")
    arquivo_log = os.path.join(LOG_FOLDER, f"{hoje}.log")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha_log = f"[{timestamp}] {mensagem}\n"

    with open(arquivo_log, "a", encoding="utf-8") as log:
        log.write(linha_log)
