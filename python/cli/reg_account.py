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
    print_header('РЕГИСТРАЦИЯ УЧЕТНОЙ ЗАПИСИ')
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
        account_info = rs.get('server.account_info', {'account_id':account_id})
        if account_info is None:
            print_error(f'Учетная запись "{account_id}" неизвестна на "{rs.domian_name}"')
        else:
            print_comment(f'{account_info.id},{account_info.alias},{account_info.description}')
            account = Account.create_or_update(account_info)
            break

    # Копирование подразделений 
    #print_comment('Синхронизация подразделений')
    depts = rs.get('server.depts', {'account_id': account.id})
    if depts is not None:
        with sqlite3.connect(DEPTS_DB) as conn:
            for dept in depts:
                Dept.insert_or_replace(conn, dept)
        databases = Databases()
        for dept in depts:
            print_comment(f'{dept.code}, {dept.name}')
            database_uri = dept.get_param(Dept.DATABASE_URI)
            if database_uri is not None:
                try:
                    database = Database.parse(database_uri)
                    databases.set_database(database, account.id, dept.guid)
                    revision = database.get_revision()
                    if revision is None:
                        print_warning(f'Недоступна БД "{database_uri}" для подразделения "{dept.code}, {dept.name}"')
                    else:
                        print_comment(f'    {database_uri} : {revision}')
                        pass
                except BaseException as ex:
                    print_warning(f'{ex}')
    else:
        print_error(f'Не найдено ни обного подразделения')        


