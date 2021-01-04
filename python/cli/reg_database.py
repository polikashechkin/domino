import os, sys, sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import Console, print_comment, arg, print_error, print_header, print_warning
from domino.databases.oracle import Databases, Database
from domino.log import log
from domino.server import Server, GUID
from domino.account import Account, DEPTS_DB, find_account, Dept, MASTER_DEPT_CODE

if __name__ == "__main__":
    c = Console()
    print('')
    print_header('РЕГИСТРАЦИЯ БАЗЫ ДАННЫХ')
    print('')
    
    # открытие регистрационного сервера
    rs = Server.reg_server()
    server_info = rs.get('server.info')
    if server_info is None:
        print_error('Не определен или не доступен регистрационный сервер')
        sys.exit()

    # Определение учетной записи
    while True:
        account_id = c.input(f'Учетная запись')
        account = find_account(account_id)
        if account is None:
            print_error(f'Учетная запись "{account_id}" не зарегистрирована на данном сервере')
        else:
            break

    # Определение подразделеная
    while True:
        print()
        c.help('Задайте подразделение для которого определяем базу данных')
        c.help('Для этого следует задачть код подразделения')
        c.help('В случае подразделения центрального офиса следует задать "."')
        print()
        dept_code = c.input(f'Подразделение')
        dept = account.find_dept(dept_code)
        if dept is None:
            print_error(f'Подразделение "{dept_code}" не зарегистрирована на данном сервере')
        else:
            break

    # Задание базы данных
    while True:
        print()
        c.help('Задайте определение базы данных в формате схема@сервер')
        print()
        database_uri = c.input(f'База данных')
        database = Database.parse(database_uri)
        if database is None:
            print_error(f'Не правильно задан формат описание базы данных')
        else:
            revision = database.get_revision()
            if revision is None:
                print_error(f'База данных "{database.uri}" недоступная на данном сервере')
            else:
                break

    # сохранение на текущем сервере
    databases = Databases()
    try:
        databases.set_database(database, account.id, dept.guid)
    except BaseException as ex:
        log.exception('reg_database')
        c.error(f'Ошибка регистрации базы данных {database} для {account.id} : {ex}')
    if dept.is_maindept :
        databases.set_database(database, account.id)

    # сохрание на сервере
    status = rs.get('server.reg_database', {'account_id': account.id, 'dept_id':dept_code, 'database':database.uri})
    if status is None:
        print_error(f'Ошибка доступа к серверу "{rs.domain_name}": "{rs.error}"')
    elif not status.success: 
        print_error(f'{status.get("message")}')
