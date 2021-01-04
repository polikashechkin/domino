import os, sys, sqlite3, requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import print_comment, arg, print_error
from domino.databases.oracle import Databases
from domino.account import DEPTS_DB, find_account, Dept
from domino.core import Server

if __name__ == "__main__":
    action = arg(1)
    if action is None:
        with sqlite3.connect(DEPTS_DB) as conn:
            for dept in Dept.findall(conn):
                database = Databases().get_database(dept.account_id, dept.guid)
                database_name = database.uri if database is not None else ''
                print(dept.account_id, dept.code, dept.name, database_name, dept.info)

    elif action == 'find':
        account_id = arg(2)
        account = find_account(account_id)
        if account is None:
            print_error(f'Учетная запись "{account_id}" не зарегистрирована на данном сервере')
            sys.exit()
        ac_domino_ru = Server.get_config().ac_domino_ru
        r = requests.get(f"https://{ac_domino_ru}/domino/active/python/get_depts", params = {"account_id":account.id})
        if r.status_code != 200:
            print_comment(r.url)
            print_error(f'Список подразделений не доступен на сервере "{ac_domino_ru}" : {r.status_code}')
            sys.exit()
        depts = r.json()
        for dept in depts:
            print(dept['guid'], dept['code'], dept['name'])
    else:
        print_error(f'Неизвестная команда "{action}"')
        
'''
    elif action == 'find':
        ac_domino_ru = Server.get_config().ac_domino_ru
        if find_account_id(account_id) is None:
            return f'Учетная запись "{account_id}" не найдена на рабочем сервере', '400'
        type_id = request.args.get('type')
        metric = Metric.get(type_id)
        if metric is None:
            return f'Неизвестный тип объекта {type_id}', '400'
        key = request.args.get('key')
        if key is None:
            return f'Не задан идентификатор объекта лицензирования', '400'
        try:
            if type_id == LOCATION:
                r = requests.get(f"https://{ac_domino_ru}/ac/active/python/get_dept_guid", params = {"account_id":account_id, "type":type_id, "code": key})
'''
        
