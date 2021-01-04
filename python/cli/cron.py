import os, sys, datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.crontab import CronTab
from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning

def helpc(command, description):
    print_help(command)
    #print(f'     {description}') 
    print(f'{description}') 
#    print()

def help():
    print()
    helpc('domino cron', 'Общий список всех заданий планировщика') 
    helpc('domino cron today [дата]', 'Показывает список процедур, запускаемых в течении заданнуой даты (неважно в какое время). Если дата не задана, то принимается текущая дата')
    helpc('domino cron add модуль.процедура[.учетка] <дни> <время>', 
        'Добавляет или изменяет запуск задачи. Дни указываются через запятую. Время в формате HH:MM:SS. Если для всех дней, то указывается "-"')
    print_help('domino cron create_if_not_exists модуль.процедура[.учетка] <дни> <время>')
    print('     Добавляет процедуру, если таковой еще не задано. Если задано то НЕ изменяет параметры расписания')
    print_help('domino cron remove модуль.процедура[.учетка]')
    print('     Удаляет процедуру из расписания планировщика')
    print_help('domino cron disable <номер>')
    print_warning('domino cron enable <номер>')
    print_warning('domino cron start модуль.процедура[.учетка]')
    print('     Запускает процедуру немедленно, вне зависимости от расписания планировщика')
    print_warning('domino cron clean <номер>')
    print('     Удаляет признак запуска процедуры')

if __name__ == "__main__":
    if arg(1) is not None and arg(1) == '--help':
        help()
        sys.exit()
    action = arg(1)
    if not CronTab.is_active():
        print_error('Планировщик не запущен, для запуска вызовите команду "domino start cron"')
    if action is None:
        cron = CronTab()
        print(f'ID  Процедура                      Дни        Время    Последний запуск Описание')
        print(f'--- ------------------------------ ---------- -------- ---------------- -----------------------------')
        for job in cron.get_jobs():
            start = job.s_start if job.s_start is not None else ''
            job_id = str(job.job_id) if job.job_id is not None else ''
            description = job.description if job.description is not None else ''
            #time = f'{job.s_time}'
            msg = f'{job.rowid:3} {job.name:30} {str(job.days):10} {str(job.times):8} {start:10} {job_id:5} {description}'
            if job.enabled:
                print(msg)
            else:
                print_comment(msg)
    elif action == 'add':
        name = arg(2)
        product_id, program, account_id = CronTab.parse_name(name)
        if not os.path.isfile(f'/DOMINO/products/{product_id}/active/python/{program}.py'):
            print_error(f'Не установлена процедура "{product_id}.{program}"')
            sys.exit()
        days = arg(3)
        time = arg(4)
        CronTab().add(product_id, program, account_id, days, time)

    elif action == 'create_if_not_exists':
        name = arg(2)
        product_id, program, account_id = CronTab.parse_name(name)
        if not os.path.isfile(f'/DOMINO/products/{product_id}/active/python/{program}.py'):
            print_error(f'Не установлена процедура "{product_id}.{program}"')
            sys.exit()
        days = arg(3)
        time = arg(4)
        CronTab().create_if_not_exists(product_id, program, account_id, days, time)

    elif action == 'remove':
        name = arg(2)
        try:
            CronTab().remove_by_rowid(int(name))
        except:
            product_id, program, account_id = CronTab.parse_name(name)
            CronTab().remove(product_id, program, account_id)

    elif action == 'disable':
        name = arg(2)
        try:
            CronTab().disable_by_rowid(int(name))
        except:
            product_id, program, account_id = CronTab.parse_name(name)
            CronTab().disable(product_id, program, account_id)

    elif action == 'enable':
        name = arg(2)
        try:
            CronTab().enable_by_rowid(int(name))
        except:
            product_id, program, account_id = CronTab.parse_name(name)
            CronTab().enable(product_id, program, account_id)

    elif action == 'start':
        name = arg(2)
        product_id, program, account_id = CronTab.parse_name(name)
        cron = CronTab()
        if cron.exists(product_id, program, account_id):
            ID = cron.start(product_id, program, account_id)
            print_comment(ID)
        else:
            print_error(f'Нет такой задачи "{name}"')

    elif action == 'today':
        cron = CronTab()
        #time_s = arg(3)
        #if time_s is not None:
        #    TIME = datetime.datetime.strptime(time_s, '%H:%M:%S')
        #else:
        #    TIME = datetime.datetime.strptime('04:00:00', '%H:%M:%S')
        TODAY = datetime.datetime.strptime(arg(2), '%Y-%m-%d').date() if arg(2) is not None else datetime.date.today()
        print_help(f'Процедуры, планруемые к запуску {TODAY:%Y-%m-%d}')
        jobs = cron.today(TODAY)
        if len(jobs) == 0:
            print("Нет таких")
        else:
            print(f'Процедура                      Дни        Время    Последний запуск *')
            print(f'------------------------------ ---------- -------- ---------------- -')
            for job in jobs:
                start = job.s_start if job.s_start is not None else ''
                job_id = job.job_id if job.job_id is not None else ''
                time = str(job.times)
            #    sign = '*' if job.check_time(TIME) else ' '
                msg = f'{job.name:30} {str(job.days):10} {time:8} {start:10} {job_id}'
                print(msg)

    elif action == 'clean':
        name = arg(2)
        try:
            CronTab().clean_by_rowid(int(name))
        except:
            product_id, program, account_id = CronTab.parse_name(name)
            CronTab().clean(product_id, program, account_id)

    else:
        print_error(f'Неизвестная команда "{action}"')
        
        
