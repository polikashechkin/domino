import os, sys, json
from domino.core import Version, DOMINO_ROOT, log as LOG
import sqlite3
from domino.jobs import Proc
import domino.crontab
import domino.account

import domino.tables.accountdb.license

def create_jobs_structure():
    domino.jobs.create_structure()
    domino.crontab.create_structure()
    os.makedirs('/DOMINO/data', exist_ok=True)
    conn = sqlite3.connect('/DOMINO/data/account.db')
    cur = conn.cursor()
    cur.execute('''
        create table if not exists databases (
            account_id text not null default (''),
            id text not null default (''),
            scheme text not null,
            host text not null,
            service_name text default ('orcl'),
            port int default 1521,
            info blob,
            primary key(account_id, id) 
        );
        '''
    )
    cur.close()
    conn.close()

def create_accounts_table():
    domino.account.create_structure()
    os.makedirs('/DOMINO/data', exist_ok=True)
    conn = sqlite3.connect('/DOMINO/data/account.db')
    cur = conn.cursor()
    cur.execute('''
        create table if not exists databases (
            account_id text not null default (''),
            id text not null default (''),
            scheme text not null,
            host text not null,
            service_name text default ('orcl'),
            port int default 1521,
            info blob,
            primary key(account_id, id) 
        );
        '''
    )
    cur.close()
    conn.close()

def create_nginx_structure():
    pass
    #print(f'/bin/cp -f -r {version_folder}/nginx.template/* /etc/nginx')
    #os.system(f'/bin/cp -f -r {version_folder}/nginx.template/* /etc/nginx' )
    #print(f'/bin/cp -f -r {version_folder}/uwsgi.template/* /DOMINO/uwsgi')
    #os.system(f'/bin/cp -f -r {version_folder}/uwsgi.template/* /DOMINO/uwsgi')
    #os.system('service nginx reload ')

if __name__ == "__main__":

    version_folder = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    try:
        info_file = os.path.join(version_folder, "info.json")
        with open(info_file, "r") as f:
            info = json.load(f)
        version = info['version']
        product = info['product']
    except:
        print('Version info not found in "{0}"'.format(version_folder))
        sys.exit(1)

    print('"{0} {1}", "{2}"'.format(product, version, version_folder))

    domino_usr = os.path.join(version_folder, 'python', 'domino.usr.py')
    cmd = 'python3.6 {0} activate domino {1}'.format(domino_usr, version)
    os.system(cmd)

    create_accounts_table()
    #create_nginx_structure()
    Proc.create('', 'domino', 'sheduler.py', CLASS=1, description='Планировщик')
    Proc.create('', 'domino', 'cleaning.py', description='Уборка', time='2:00')
    #Proc.create('', 'domino', 'startup.py', CLASS=2, description='Запуск системы')

    domino.tables.accountdb.license.on_install(print)
