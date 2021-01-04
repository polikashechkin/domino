import os, sys, sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import print_comment, arg, print_error, print_header, print_warning
from domino.databases.oracle import Databases, Database
from domino.account import DEPTS_DB, find_account, ACCOUNTS_DB, Dept

def help():
    print()
    print_header('Вызов:')
    print('  domino dept <учетная запись>[.<подраздление>] [команда] [параметры]')
    print_header('Команды:')
    print('  команда не задана             Показывает описание подразделения')
    print('  database [описание]           Задает/показывает базу данных')
    print('  remove                        Удаляет подразделение с данного сервера')
    print()

if __name__ == "__main__":
    if arg(1) is not None and (arg(1) == '--help' or arg(1) == '?'):
        help()
        sys.exit()
    account_id = arg(1)
    try:
        account_id, dept_id = account_id.split('.')
    except:
        dept_id = '.'
    account = find_account(account_id)
    if account is None:
        print_error(f'Учетная запись "{account_id}" не зарегистрирована на данном сервере')
        sys.exit()
    #print_comment(account.id)
    dept = account.find_dept(dept_id)
    if dept is None:
        print_error(f'Подразделение "{account.id}.{dept_id}" не зарегистрировано на данном сервере')
        sys.exit()
    #print_comment(dept.guid)
    action = arg(2)        
    if action is None:
        print()
        print('GUID         ', dept.guid)
        print('Код          ', dept.code)
        print('Наименование ', dept.name)
        print('Адрес        ', dept.address)
        database = Databases().get_database(account.id, dept.guid)
        print('База данных  ', database.uri if database is not None else 'Не определена')
        print()
    elif action == 'database':
        databases = Databases()
        database_uri = arg(4)
        if database_uri is None:
            database = databases.get_database(account.id, dept.guid)
            if database is not None:
                print(database.uri)
        else:
            database = Database.parse(database_uri)
            if database is None:
                print_error('Не правильно задано описание БД "{database_uri}"')
            else:
                revision = database.get_revision()
                if revision is None:
                    print_error('Не обнаружено базы данных "{database.uri}" на данном сервере')
                else:
                    databases.set_database(database, account.id, dept.guid)
    elif action == 'remove':
        databases = Databases()
        guid = dept.guid
        databases.remove(account.id, guid)
        print()
        print_warning(f'Удалена база данных "{account_id}.{guid}"')
        with sqlite3.connect(ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            Dept.delete(cur, account.id, dept.guid)
            print_warning(f'Удалено подразделение "{account_id}.{dept.code}"')
        print()

    else:
        print_error(f'Неизвестная команда "{action}"')
    