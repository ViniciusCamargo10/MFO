import schedule
import time

HORARIOS = ["08:00", "16:00"]


def configurar(job_func):
    for horario in HORARIOS:
        schedule.every().day.at(horario).do(job_func)


def iniciar():
    while True:
        schedule.run_pending()
        time.sleep(30)
