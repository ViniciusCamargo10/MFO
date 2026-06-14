import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.logger import registrar_execucao
from src.dou_scraper import acessar_dou
from src.scheduler import configurar, iniciar


def executar():
    print(f"Iniciando execução...")
    sucesso, mensagem = acessar_dou()
    if sucesso:
        registrar_execucao(status="SUCESSO", info=mensagem)
        print(f"OK - {mensagem}")
    else:
        registrar_execucao(status="FALHA", erro=mensagem)
        print(f"FALHA - {mensagem}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        executar()
        return

    configurar(executar)
    print(f"Agendador iniciado. Horários: {', '.join(['08:00', '16:00'])}")
    iniciar()


if __name__ == "__main__":
    main()
