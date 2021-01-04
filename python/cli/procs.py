import os, sys, datetime, sqlite3, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from domino.core import log, DOMINO_ROOT
from domino.account import find_account_id
from domino.jobs import Proc

#from domino.crontab import CronTab
from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning

def helpc(command, description):
    print_help(command)
    #print(f'     {description}') 
    print(f'{description}') 
#    print()

def help():
    print('domino procs list                                        : Список процедур') 
    print('domino procs create <account_id> <module> <proc>         : Создать процедуру')
    print('domino procs create_service <account_id> <module> <proc> : Создать сервисную процедуру')
    print('domino procs delete <номер>                              : Удалить процедуру')
    print('domino procs enable <номер>                              : Статус endbled (+)')
    print('domino procs disable <номер>                             : Статус disabled (-)')
    print('domino procs start <номер>                               : Запуск процедуры')

if __name__ == "__main__":
    if arg(1) is not None and arg(1) == '--help':
        help()
        sys.exit()
    action = arg(1)
    
    #jobs = Proc.jobs(Proc.NO_ACCOUNT_ID, 'domino','sheduler', STATE=[0])

    if action is None:
        help()

    elif action == 'list':
        print(f'ID   CLASS  STATE account_id module               proc                 autostart    last_job')
        print(f'---- ------ ----- ---------- -------------------- -------------------- ------------ --------')
        conn = sqlite3.connect(os.path.join(DOMINO_ROOT, 'data', 'jobs.db'))
        cur = conn.cursor()
        sql = 'select ID, CLASS, TYPE, STATE, account_id, module, proc, INFO from procs'
        cur.execute(sql)
        procs = cur.fetchall()
        for ID, CLASS, TYPE, STATE, account_id, module, proc, INFO in procs:
            info = json.loads(INFO)
            AUTOSTART = info.get('TIME', '') + ' ' + info.get('DAYS', '')
            ACCOUNT_ID = account_id if account_id else '-'
            CLASS_NAME = ''
            if CLASS == 1:
                CLASS_NAME = 'Сервис'
            STATE_NAME = '+'
            if STATE == 1:
                STATE_NAME = '-'
            job_ID, job_STATE, START_DATE = Proc._last_job(cur, ID)
            job_STATE = Proc.Job.state_name(job_STATE)
            if job_ID is not None:
                LAST_JOB = f'{job_ID}({job_STATE}) {START_DATE}'
            else:
                LAST_JOB = ''
            msg = f'{ID:4} {CLASS_NAME:6} {STATE_NAME:5} {ACCOUNT_ID:10} {module:20} {proc:20} {AUTOSTART:12} {LAST_JOB}'
            print(msg)

    elif action == 'create':
        ACCOUNT_ID = arg(2).strip()
        MODULE = arg(3).strip()
        PROC = arg(4).strip()
        if ACCOUNT_ID.lower() == '-':
            account_id = ''
        else:
            account_id = find_account_id(ACCOUNT_ID)
            if account_id is None:
                print(f'Не найдена учетная запись "{ACCOUNT_ID}"')
                sys.exit(1)
        ID = Proc.create(account_id, MODULE, PROC)
        print(f'Создана процедура с номером {ID}')

    elif action == 'create_service':
        ACCOUNT_ID = arg(2).strip()
        MODULE = arg(3).strip()
        PROC = arg(4).strip()
        if ACCOUNT_ID.lower() == '-':
            account_id = ''
        else:
            account_id = find_account_id(ACCOUNT_ID)
            if account_id is None:
                print(f'Не найдена учетная запись "{ACCOUNT_ID}"')
                sys.exit(1)
        ID = Proc.create(account_id, MODULE, PROC, CLASS = Proc.CLASS_SERVICE)
        print(f'Создана процедура с номером {ID}')

    elif action == 'delete':
        ID = int(arg(2))
        Proc.delete(ID)
        print(f'Удалена процедура с номером {ID}')

    elif action == 'enable':
        ID = int(arg(2))
        Proc.change_state(ID, Proc.STATE_ENABLED)
        print(f'Устатновлен статус (+) для процедуры с номером {ID}')

    elif action == 'disable':
        ID = int(arg(2))
        Proc.change_state(ID, Proc.STATE_DISABLED)
        print(f'Устатновлен статус (-) для процедуры с номером {ID}')

    elif action == 'start':
        ID = arg(2)
        Proc.start_by_id(ID)
        #print (f'Запучена задача')

    elif action == 'clean':
        ID = arg(2)
        count = Proc.clean(ID)
        print (f'Удалено {count} задач')

    elif action == 'autostart':
        ID = arg(2)
        TIME = arg(3)
        DAYS = arg(4)
        count = Proc.autostart(ID, TIME, DAYS)
    else:
        print_error(f'Неизвестная команда "{action}"')
        
        
