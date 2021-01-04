import os, sys, sqlite3, re, psutil, shutil, psycopg2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.databases.postgres import Postgres
from domino.cli import Console 
from domino.databases.oracle import Databases, Database
from domino.core import log, Version
from domino.server import Server, GUID
from domino.account import Account, DEPTS_DB, find_account, Dept, MASTER_DEPT_CODE, AccountConfig

c = Console()


#    account = find_account(account_id)
#    if account is None:
#        c.error(f'Учетной записи "{account_id}" не обнаружено на данном сервере')
#        print_error
#    action = c.arg(2)
#    c.run(product, version, 'on_activate', [account.id])

def config(pg_version):
    MB = 1024 * 1024
    mem = psutil.virtual_memory()
    total_mb = int(mem[0] / MB)
    shared_buffers = re.compile(r'^[# ]*(shared_buffers)')
    mem_mb = int(total_mb/4)


    postgresql_conf = f'/var/lib/pgsql/{pg_version}/data/postgresql.conf'
    if os.path.isfile(postgresql_conf):
        c.print_comment(postgresql_conf)
        c.print_comment(f'Общий размер памяти {total_mb} МБ')
        c.print_comment(f'Рекомендуемые для posgres {mem_mb} МБ')
        shutil.copyfile(postgresql_conf, f'{postgresql_conf}.bak')
        lines = []
        with open(postgresql_conf) as f:
            for line in f:
                lines.append(line)
                #line.replace('\n', '')
                #if shared_buffers.match(line):
                #    c.print_help(line.replace('\n', ''))
        
        for i in range(len(lines)):
            if shared_buffers.match(lines[i]):
                lines[i] = f'shared_buffers = {mem_mb}MB\n'

        with open(postgresql_conf, 'w') as f:
            for line in lines:
                f.write(line)

        #c.print_comment(postgresql_conf)
        with open(postgresql_conf) as f:
            for line in f:
                if shared_buffers.match(line):
                    c.print_help(line.replace('\n', ''))

def external():
    c.print_header('POSTGRES EXTERNAL')

def get_account(account_id):
    if not account_id:
        c.error('Не задана учетная запись')
        sys.exit(1)
    else:
        account = find_account(account_id)
        if not account:
            c.error('Не найдена учетная запись "{account_id}"')
            sys.exit(1)
    return account

def postgres_restart():
    cmd = f'systemctl restart postgresql-11'
    c.print_comment(cmd)
    os.system(cmd)

if __name__ == "__main__":
    action = c.arg(1)
    if not action:
        print('Вызов: domino posgres [команда]')
        print()
        print('команды:')
        print(f'  config                           конфигурирование')
        print(f'  external                         настроить внешний доступ')
        print(f'  create_database  <account_id>    создать баду данных')
        print(f'  drop_database    <account_id>    удалить баду данных')
        print(f'  restart                          перезагрузить postgres')
        print()
        sys.exit(1)
    action = action.strip().lower()
    if action == 'config':
        #c.print_header('POSTGRES CONFIG')
        config(12)
        config(11)
    elif action == 'external':
        external()
    elif action == 'create_database':
        account = get_account(c.arg(2))
        Postgres.create_database(account.id, print)
    elif action == 'drop_database':
        account = get_account(c.arg(2))
        postgres_restart()
        Postgres.drop_database(account.id, print)
    elif action == 'restart':
        postgres_restart()
    else:
        c.print_header('POSTGRES')
        c.error(f'Неизвестная команда "{action}"')
