import os, sys, psutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import print_comment, print_error, Console, arg
from domino.jobs import JobReport, Job
import domino.jobs as jobs

if __name__ == "__main__":
    ID = arg(1)
    c = Console()
    if ID is None:
        c.error(f'Не задан идентификатор задачи')
    try:
        job = JobReport(ID)
    except:
        c.error(f'Задача {ID} не обнаружена')
    action = arg(2)
    if action is None:
        if job.status == -1:
            state = 'Инициализация'
        elif job.status == 0:
            pid = job.pid
            if pid is not None and not psutil.pid_exists(pid):
                state = f'Брошена ({pid})' 
            else:
                state = f'В работе ({pid})' 
        elif job.status == Job.Error:
            state = 'Заверешена с ошибкой'
        elif job.status == Job.Success:
            state = 'Заверешена успешно'
        else:
            state = job.state
            
        print(f'Задача           : {job.id} ({job.name})')
        print(f'Процедура        : {job.product_id}')
        print(f'Начало работы    : {job.start}')
        print(f'Состояние        : {state}')
        print(f'Описание         : {job.description}')
        if os.path.exists(jobs.job_break_file(ID)):
            c.warning(f'Запрос на прерывание')
    elif action == 'stop':
        jobs.stop_job(ID)
    else:
        print_error(f'Неизвестная команда "{action}"')

