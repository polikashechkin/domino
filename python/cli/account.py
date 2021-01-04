import os, sys, sqlite3, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import Console, print_comment, arg, print_error, print_header, print_warning
from domino.databases.oracle import Databases, Database
from domino.core import log, Version, DOMINO_ROOT
from domino.server import Server, GUID
from domino.account import Account, DEPTS_DB, find_account, Dept, MASTER_DEPT_CODE, AccountConfig

if __name__ == "__main__":
    c = Console()
    account_id = c.arg(1)
    account = find_account(account_id)
    if account is None:
        c.error(f'Учетной записи "{account_id}" не обнаружено на данном сервере')
        print_error
    action = c.arg(2)
    if action is None:
        print(f'Идентификатор  {account.id}')
        print(f'Псевдоним      {account.alias}')
        print(f'Пароль         {account.password}')
        print(f'Наименование   {account.description}')
        print(f'База данных    {account.get_database_uri()}')
        print(f'Конфигурация   {account.config_id}')

    elif action == 'activate':
        product = c.arg(3)
        if product is None:
            c.error(f'Не задан продукт')

        # Определение версии
        ver = c.arg(4)
        if ver is None:
            # если версия не задана, то берем текущую активную версию
            version_info_file = os.path.join(DOMINO_ROOT, 'products', product, 'active', 'info.json')
        else:
            version_info_file = os.path.join(DOMINO_ROOT, 'products', product, ver, 'info.json')
        
        if not os.path.isfile(version_info_file):
            c.error(f'Нет файла {version_info_file}')
        
        with open(version_info_file) as f:
            version_info = json.load(f)

        #print(f'{version_info}')
        version = Version.parse(version_info['version'])
        if version is None:
            c.error(f'Продукт "{product}" версия "{ver}" не установлен или не активирован на данном сервере')
        print(f'Версия {version}')
        # --------------------
        config = AccountConfig.load(account)
        config.add(product)
        AccountConfig.save(config, account)
        c.run(product, version, 'on_activate', [account.id])

    elif action == 'products':
        config = AccountConfig.load(account)
        if len(config.products) == 0:
            print_warning(f'Для данной учетной записи не задано ни одного продукта')
        else:
            for product in config.products:
                print(product.id, product.version)

    elif action == 'depts':
        for dept in account.find_depts():
            print(f'{dept.code} {dept.name}')

    elif action == 'alias':
        alias = c.arg(3)
        if alias is None:
            print(account.alias)
        else:
            account.alias = alias

    else:
        c.error(f'Неизвестная команда "{action}" ')
