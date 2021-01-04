import os, sys, psutil, arrow
import os, sys, datetime, sqlite3, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from domino.core import log, DOMINO_ROOT
from domino.account import find_account_id
from domino.jobs import Proc, Job

from domino.cli import print_comment, print_error, Console, arg


def print_jobs(jobs):
    print(f'#     state start               proc_id')
    print(f'----- ----- ------------------- -------') 
    for ID, STATE, START, PROC_ID in jobs:
        if STATE == 0:
            STATE = 'A'
        elif STATE == -1:
            STATE = 'Q'
        try:
            start = arrow.get(START)
            START = start.format('YYYY-MM-DD HH:mm:ss')
        except:
            START = ''
        #print(ID, CLASS, TYPE, STATE, ACCOUNT_ID, PRODUCT_ID, PROGRAMM)  
        #ACCOUNT_ID = ACCOUNT_ID if ACCOUNT_ID else ''
        #MODULE = MODULE if MODULE else ''
        START = START if START else ''
        print(f'{ID:5} {STATE:5} {START:19} {PROC_ID:7}')

if __name__ == "__main__":
    action = arg(1)
    Proc.Job.check()
    if action is None:
        help()
    elif action == 'list':
        with Proc.connect() as conn:
            cur = conn.cursor()
            cur.execute('select ID, STATE, START_DATE, PROC_ID from proc_jobs order by START_DATE')
            jobs = cur.fetchall()
        print_jobs(jobs)

    elif action == 'active':
        with Proc.connect() as conn:
            cur = conn.cursor()
            cur.execute('select ID, STATE, START_DATE, PROC_ID from proc_jobs where STATE = 0')
            jobs = cur.fetchall()
        print_jobs(jobs)

    elif action == 'delete':
        ID = arg(2)
        Proc.Job.delete(ID)
        print(f'Удалена задача {ID}')

    elif action == 'stop':
        ID = arg(2)
        Proc.Job.stop(ID)
        print(f'Останов задачи {ID}')

    elif action == 'log':
        ID = arg(2)
        log = Proc.Job.read_log(ID)
        print(log)

    else:
        print(f'неизвестная команда {action}')

