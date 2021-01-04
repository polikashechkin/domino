import os, sys, sqlite3, json, requests, pickle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import print_comment, arg, print_error, print_header, print_warning
from domino.databases import Databases, Database
from domino.core import log, DOMINO_ROOT
from domino.server import Server, GUID
from domino.account import Account, DEPTS_DB, find_account, Dept, MASTER_DEPT_CODE

SERVER_CONFIG = {}
SERVER_CONFIG_FILE = os.path.join(DOMINO_ROOT, 'domino.config.info.json')

def get_reg_server():
    return SERVER_CONFIG.get('ac_domino_ru', '')

def get_account_id():
    return SERVER_CONFIG.get('account_id', '')

def GET(proc, params = {}, product_id = 'domino'):
    url = f'https://{get_reg_server()}/{product_id}/active/python/{proc}'
    r = requests.get(url, params, stream=True)
    print_comment(r.url)
    #self.url = r.url
    #self.status_code = r.status_code
    if r.status_code != 200:
        print(r.url)
        print_error(r.status_code)
        print_error(r.text)
        #self.error = r.text
            #print(f'{r.status_code} : {r.url}')
        return None
    return pickle.loads(r.raw.read())

def save_config():
    with open(SERVER_CONFIG_FILE, 'w') as f:
        json.dump(SERVER_CONFIG, f, ensure_ascii=False)

if __name__ == "__main__":
    print('')
    print_header('РЕГИСТРАЦИЯ СЕРВЕРА')
    print('')
    #print (SERVER_CONFIG_FILE)

    if os.path.exists(SERVER_CONFIG_FILE):
        with open(SERVER_CONFIG_FILE) as f:
            SERVER_CONFIG = json.load(f)

    #print (SERVER_CONFIG)
    
    # Определение или переопределение доменного имени регистрационного сервера
    while True:
        rs_domain_name = input(f'Адрес регистрационного сервера [{get_reg_server()}] ? ').strip()
        if rs_domain_name != '':
            SERVER_CONFIG['ac_domino_ru'] = rs_domain_name
            save_config()

        server_info = GET('server.info')
        if server_info is None:
            print_error(f'''Нет сервера "{get_reg_server()}"''')
        else:
            print(f'{server_info.name}')
            break

    # Определение или переопределения учетной записи для сервера
    while True:
        account_id = input(f'Основная учетная запись [{get_account_id()}] ? ').strip()
        if account_id != '':
            SERVER_CONFIG['account_id'] = account_id
            save_config()
        account_info = GET('server.account_info', {'account_id':get_account_id()})
        if account_info is None:
            print_error(f'Учетная запись "{get_account_id()}" неизвестна на "{get_reg_server()}"')
        else:
            SERVER_CONFIG['account_id'] = account_info.id
            save_config()
            print(f'{account_info.id},{account_info.alias},{account_info.description}')
            account = Account.create_or_update(account_info)
            break
    '''
    # Определение основного подразделения 
    # Пока упрощение - только головной сеовео регистрируем
    main_dept = rs.get('server.dept', {'account_id':account.id, 'dept_id':MASTER_DEPT_CODE})
    if main_dept is None:
        print_error(f'Для учетной записи не задано подразделения')
        sys.exit()
    if main_dept.get_param(Dept.DATABASE_URI) is None:
        print_warning(f'Не определена база данных для подразделения "{main_dept.name}"')
    server_guid = main_dept.get_param(Dept.SERVER_GUID)
    if server_guid is not None and server_guid != GUID:
        print_warning(f'уже есть регистрация сервера центрального офиса')
    status = rs.get('server.reg_server', {
        'account_id': account.id, 'server_id':GUID, 'dept_id' : MASTER_DEPT_CODE
        })
    if status is None:
        print_error(f'Ошибка доступа к серверу {rs.domian_name}')
        sys.exit()
    if not status.success:
        message = status.get('message')
        print_error(f'{message}')
        sys.exit()
    '''
    # Копирование подразделений 
    '''
    print('Синхронизация подразделений')
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
    '''
            


