import json
import os
from datetime import datetime


LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "execucao.jsonl")


def registrar(data_hora: str, status: str, erro: str = "", info: str = ""):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "data_hora": data_hora,
        "status": status,
        "erro": erro,
        "info": info,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def registrar_execucao(status: str, erro: str = "", info: str = ""):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registrar(agora, status, erro, info)
