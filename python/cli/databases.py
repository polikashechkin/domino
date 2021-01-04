import os, sys, datetime, sqlite3, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from domino.core import log, DOMINO_ROOT
from domino.account import find_account_id
from domino.databases.oracle import Database

#from domino.crontab import CronTab
from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning

def helpc(command, description):
    print_help(command)
    #print(f'     {description}') 
    print(f'{description}') 
#    print()

def help():
    print('domino databases list                                    : Список баз данных') 
    print('domino databases test <номер>                            : Проверить БД')

if __name__ == "__main__":
    if arg(1) is not None and arg(1) == '--help':
        help()
        sys.exit()
    action = arg(1)
    
    if action is None:
        help()

    elif action == 'list':
        print(f'#    ACCOUNT_ID  GUID                                 DSN  ')
        print(f'---- ----------- ------------------------------------ ----------------------- ')
        conn = sqlite3.connect(os.path.join(DOMINO_ROOT, 'data', 'account.db'))
        cur = conn.cursor()
        sql = 'select ROWID, ACCOUNT_ID, ID, HOST, SCHEME, PORT, SERVICE_NAME from databases'
        cur.execute(sql)
        databases = cur.fetchall()
        for ROWID, ACCOUNT_ID, ID, HOST, SCHEME, PORT, SERVICE_NAME in databases:
            print(f'{ROWID:4} {ACCOUNT_ID:12} {ID:40} {SCHEME}@{HOST}:{PORT}/{SERVICE_NAME}')

    elif action == 'test':
        ROWID = arg(2)
        conn = sqlite3.connect(os.path.join(DOMINO_ROOT, 'data', 'account.db'))
        cur = conn.cursor()
        sql = 'select ROWID, ACCOUNT_ID, ID, HOST, SCHEME, PORT, SERVICE_NAME from databases where rowid=? '
        cur.execute(sql, [ROWID])
        r = cur.fetchone()
        if r is None:
            print('НЕТ ТАКОЙ БД')
            sys.exit(1)
        ROWID, ACCOUNT_ID, ID, HOST, SCHEME, PORT, SERVICE_NAME = r
        print(f'{ACCOUNT_ID}.{ID}')
        database = Database(SCHEME, HOST, PORT, SERVICE_NAME)
        print(database.dsn)
        revision = database.get_revision()
        if revision is None:
            print('НЕДОСТУПНА')
        else:
            print(f'Версия {revision}')

    else:
        print_error(f'Неизвестная команда "{action}"')
        
        
