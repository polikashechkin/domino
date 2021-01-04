#!/usr/bin/python3.6
import sys, os, shutil, json, re, locale, platform
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
#print('Привет')
import cx_Oracle, requests
import sqlite3
from glob import glob
import psutil 
#from python_hosts.hosts import Hosts, HostsEntry

from domino.core import log, Version, Server, Config

from domino.globalstore import GlobalStore
from domino.account import Account, find_account, find_account_id
from domino.hosts import Hosts
from domino.databases.oracle import Databases, Database
from domino.cli import print_header, print_error, print_comment, print_warning, bcolors

import importlib

#sys.path.insert(0, '/DOMINO/products')
'''
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    COMMENT = '\033[90m'

def print_comment(text):
    print('\033[90m' + text + '\033[0m')
def print_error(text):
    print('\033[91m' + text + '\033[0m')
def print_header(text):
    print('\033[1m' + text + '\033[0m')
def print_warning(text):
    print('\033[93m' + text + '\033[0m')
'''

def symlink(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)
    #print('create symlink "{0}" to "{1}"'.format(dst, src))

def arg(n):
    try:
        #return sys.argv[n].lower()
        return sys.argv[n]
    except:
        return None
def arglist(n):
    r = []
    while ARG(n) is not None:
        r.append(ARG(n))
        n += 1
    return r
       
def ARG(n):
    try:
        return sys.argv[n]
    except:
        return None

class Query:
    def __init__(self, query):
        if query is None:
            self.query = None
            self.defined = False
        else:
            self.defined = True
            self.query = query.lower().strip()
        self.match = False

    def test(self, value):
        if self.defined:
            if value is None: 
                return
            print(f'{self.query} in {value}')
            if value.lower().find(self.query) != -1:
                self.match = True

class ACCOUNT:
    @staticmethod
    def list(query = None):
        #print_warning(f'{query}')
        if query is not None:
            #print_warning(f'{query}')
            query = re.compile('.*' + query, re.I)
        #query  = Query(query)
        for account in Account.findall(query):
            account_id = account.id
            alias = account.alias
            if alias is None:
                alias = ''
            description = account.description
            #query.match = False
            #query.test(account_id)
            #query.test(alias)
            #query.test(description)
            #if query.match:
            if alias.strip() == '':
                id = f'{account_id}'
            else:
                id = f'{account_id}({alias}) '
            msg = f'{id:20}\t{description}'
            if query is not None:
                #print_warning(f'{query}')
                if query.match(msg) is None:
                    #print_comment(msg)
                    continue
            print(msg)

    @staticmethod
    def config(account_id, config_id):
        account = find_account(account_id)
        if account is not None:
            if config_id is not None:
                account.config_id = config_id
                config = Config(config_id)
                config.save()
            print(f'{account.config_id}')

    @staticmethod
    def install(account_id):
        if account_id is None:
            print('Не задан идентификатор учетной записи')
            return
        account_id = account_id.strip()
        if account_id == '':
            print('Не задан идентификатор учетной записи')
            return
        Account.create(account_id)

def remove_uwsgi_socket(product, version, sock_name = None):
    os.makedirs('/DOMINO/uwsgi/sockets', exist_ok=True)
    os.makedirs('/DOMINO/uwsgi/vassals', exist_ok=True)
    if sock_name is None:
        sock_name = str(version)
    sock = f'/DOMINO/uwsgi/sockets/{str(product)}.{sock_name}.sock'
    if os.path.exists(sock):
        os.remove(sock)
    vassal = f'/DOMINO/uwsgi/vassals/{str(product)}.{sock_name}.ini'
    if os.path.exists(vassal):
        os.remove(vassal)
        
def create_uwsgi_socket(product, version, sock_name = None):
    log.info(f'create uwsgi socket {product} {version} {sock_name}')
    #print(f'create uwsgi socket {product} {version} {sock_name}')
    os.makedirs('/DOMINO/uwsgi/sockets', exist_ok=True)
    os.makedirs('/DOMINO/uwsgi/vassals', exist_ok=True)
    if sock_name is None:
        sock_name = str(version)
    sock = f'/DOMINO/uwsgi/sockets/{str(product)}.{sock_name}.sock'
    vassal = f'/DOMINO/uwsgi/vassals/{str(product)}.{sock_name}.ini'
    with open(vassal, 'w') as f:
        f.write(f'[uwsgi]\n')
        f.write(f'chdir = /DOMINO/products/{product}/{version}/python\n')
        f.write(f'socket = {sock}\n')
        f.write(f'touch-reload = /DOMINO/products/{product}/{version}/python/application.py\n')
        f.write(f'python-autoreload=1\n')
        
def is_active(product, version):
    '''
    Проверяет, является ли данная верси активной в настоящий момнет
    '''
    config = Server.get_config()
    active = config.get_version(product)
    if active is None:
        return False
    return version == active

def execute_py(file_py, version = ''):
    if os.path.isfile(file_py):
        os.system(f'python3.6 {file_py} {version}')

def remove(product, version):
    if version.is_draft:
        print('макет')
        return
    if is_active(product, version):
        print('активная версия')
        return
    remove_uwsgi_socket(product, version)
    shutil.rmtree(Server.version_folder(product, version))
    print(f'Версия "{product}.{version}" удалена')

def clean(product):
    '''
    Удаляет не нужные версии продуктов. 
    НЕ УДАЛАЯЕТ МАКЕТЫ и ПОСЛЕДНИЕ ВЕРСИИ и АКТИВНЫЕ ВЕРСИИ
    '''
    last_version = None
    for version in Server.get_versions(product):
        if version.is_draft: continue
        if is_active(product, version): continue
        if last_version is None:
            last_version = version
        elif last_version > version:
            remove(product, version)
        else:
            remove(product, last_version)
            last_version = version

def clean_all():
    for product in Server.get_products():
        clean(product)

def PRODUCTS():
    for product in Server.get_products():
        versions = ' '.join(sorted(v.id for v in Server.get_versions(product)))
        print(f'{product}\t{versions}')

def PRODUCT(product):
    for version in sorted(Server.get_versions(product)):
        info = Server.get_version_info(product, version)
        if info is None:
            creation_time = "?"
        else:
            creation_time = info.creation_time

        print(f'{version}\t{creation_time}')
        
class CONFIG:
    @staticmethod
    def _print_config_product(config, product_id):
        version = config.get_version(product_id)
        print(f'{product_id}.{version}')

    @staticmethod
    def config(id, product_id, version):
        if id is None: return
        config = Config.get(id)
        if config is None: 
            print('None')
            return

        print()
        print('nn  Продукт              Весия     ')
        print('--- -------------------- ----------')
        if product_id is None:
            for n, product in config.products.items():
                print('{0:3} {1:20} {2}'.format(n, product["id"], product["version"]))
            print()

        elif version is None:
            CONFIG._print_config_product(config, product_id)

        elif version == "+":
            latest = Server.get_latest_version(product_id)
            if latest is None:
                print(f'Нет пожходящей версии для "{product}""')
            else:
                config.set_version(product, latest)
                config.save()
                SERVER.restart()
                CONFIG._print_config_product(config, product)
        elif version == "-":
            config.set_version(product_id, None)
            config.save()
            SERVER.restart()
            CONFIG._print_config_product(config, product)

class NGINX:
    @staticmethod
    def start():
        os.system('service nginx start')
    @staticmethod
    def stop():
        os.system('service nginx stop')
    @staticmethod
    def restart():
        os.system('service nginx restart')

class UWSGI:
    @staticmethod
    def start():
        os.system('uwsgi --ini /DOMINO/uwsgi/uwsgi.emperor.ini')
    @staticmethod
    def stop():
        os.system('uwsgi --stop /DOMINO/uwsgi/uwsgi.pid')
    @staticmethod
    def clear_log():
        os.remove('/DOMINO/uwsgi/uwsgi.log')
    @staticmethod
    def reload():
        os.system('uwsgi --reload /DOMINO/uwsgi/uwsgi.pid')


def help(version):
    hostname = platform.uname().node
    print_header(f'{version} {hostname}')
    print('')
    print('reg_server                          Регистрация сервера')
    print('reg_account                         Регистрация учетной записи на сервере')
    print('reg_database                        Регистрация БД для учетной записи на сервере')
    print()
    print('accounts                            Список учетных записей на сервере')
    print('account <account> [параметры]       Управление учетной записи')
    print('depts                               Список подраздлений на сервере')
    print('dept <account>[.<dept>] ...         Операции с подразделением на сервере')
    print('dept ?                              Справка')
    print()
    print('uwsgi [stop|start|reload|log]       Управление сервисом UWSGI')
    print('hosts                               Информация о /eyc/hosts')
    print()
    print('update <модуль> <версия>            Обновляет указанный модуль до заданной версии')
    print('install <модуль> <версия>           Установка версии проукта (загрузка и подготовка к активации')
    print('on_activate <модуль> <версия>       Подготовка к активации (создание модели данных) для всех учетных записей')
    print('activate <модуль> <версия>          Активация уже установленной и подготовленной версии')
    print()
    print('products                            Список установленных продуктов')
    print('product <пролукт>                   Информация ро продукте' )
    print('remove_host <имя1> .. <имяN>        Удаление всех перенаправления для списка имен')
    print('add_host <адрес> <имя1> .. <имяN>   Добавление переназначения для списка имен')
    print('set_account_alis ACCOUNT ALIAS      Задания псевдонима')
    print('set_account_password ACCOUNT ПАРОЛЬ Задания параоля')
    print('account_params account            Список параметров')
    print('set_account_param ACCOUNT ПРОДУКТ КЛЮЧ ЗНАЧЕНИЕ ')
    print('remove_account_param ACCOUNT ПРОДУКТ КЛЮЧ')
    print('add_database                        Добавить/изменить базу данных')
    print('remove_database                     Удалтьб базу данных')
    print('databases                           Список баз данных')
    print('')

if __name__ == "__main__":

    python_folder = os.path.dirname(os.path.realpath(__file__))
    version_folder = os.path.dirname(python_folder)

    try:
        info_file = os.path.join(version_folder, "info.json")
        with open(info_file, "r") as f:
            info = json.load(f)
        version = info['version']
        product = info['product']
    except:
        print('Version info not found in "{0}"'.format(version_folder))
        sys.exit()

    action = arg(1)
    if action is None:
        help(version)
        sys.exit()
    
    if action.find('.') != -1:
        product_id, programm = action.split('.')
        args = ' '.join(arglist(2))
        #print(args)
        file_py = f'/DOMINO/products/{product_id}/active/python/{programm}.py'
        command = f'python3.6 {file_py} {args}'
        print_comment(command)
        os.system(command)
        sys.exit()

    if action == 'version':
        config = Server.get_config()
        version = config.get_version('domino')

    elif action == 'on_install':
        version = Version.parse(arg(3))
        on_install(arg(2), version)

    elif action == 'remove':
        version = Version.parse(arg(3))
        remove(arg(2), version)

    elif action == 'clean':
        if arg(2) is None:
            for product in Server.get_products():
                clean(product)

    elif action == 'uwsgi':
        mode = arg(2)
        if mode == 'start':
            UWSGI.start()
        elif mode == 'stop':
            UWSGI.stop()
        elif mode == 'reload':
            UWSGI.reload()
        elif mode == 'log':
            os.system('tail -100 /DOMINO/uwsgi/uwsgi.log')
        else:
            print(f'Неизвестный паарметр {mode}')
            
    elif action == 'restart':
        UWSGI.stop()
        NGINX.stop()
        UWSGI.clear_log()
        UWSGI.start()
        NGINX.start()

    elif action == 'products':
        PRODUCTS()

    elif action == 'product':
        PRODUCT(arg(2))

    elif action == 'hosts':
        Hosts.print()

    elif action == 'add_host':
        hosts = Hosts()
        address = arg(2)
        if address is None:
            print('Не определен адрес')
            sys.exit()
        else:
            for i in range(3, 100):
                name = ARG(i)
                if name is None:
                    break
                hosts.add(address, name)
        hosts.save()
        Hosts.print()

    elif action == 'remove_host':
        hosts = Hosts()
        for i in range(2, 100):
            name = ARG(i)
            if name is None:
                break
            hosts.remove(name)
        hosts.save()
        Hosts.print()

    elif action == 'set_account_alias':
        account = find_account(arg(2))
        if account is None:
            print(f'Неизвестная учетная запись {arg(2)}')
        alias = arg(3)
        if alias is None:
            print(f'Псевдоним не задан')
        account.alias = alias

    elif action == 'set_account_password':
        account = find_account(arg(2))
        if account is None:
            print(f'Неизвестная учетная запись {arg(2)}')
            sys.exit()
        password = arg(3)
        if password is None:
            print(f'Пароль не задан')
            sys.exit()
        account.password = password

    elif action == 'account_params':
        account = find_account(arg(2))
        if account is None:
            print(f'Неизвестная учетная запись {arg(2)}')
            sys.exit()
        for product_id, key, value in account.product_params():
            print(f'{product_id:12} {key:20} {value}') 

    elif action == 'set_account_param':
        account = find_account(arg(2))
        if account is None:
            print_error(f'Неизвестная учетная запись {arg(2)}')
            sys.exit()
        product_id = arg(3)
        if product_id is None:
            print_error(f'Не задано имя продукта')
            sys.exit()
        key = arg(4)
        if key is None:
            print_error(f'Не задано имя параметра')
            sys.exit()
        value = " ".join(arglist(5))
        account.set_product_param(product_id, key, value)

    elif action == 'remove_account_param':
        account = find_account(arg(2))
        if account is None:
            print_error(f'Неизвестная учетная запись {arg(2)}')
            sys.exit()
        product_id = arg(3)
        if product_id is None:
            print_error(f'Не задано имя продукта')
            sys.exit()
        key = arg(4)
        if key is None:
            print_error(f'Не задано имя параметра')
            sys.exit()
        account.remove_product_param(product_id, key)

    elif action == 'account_create':
        account_id = arg(2)
        if account_id is None:
            print('Вызов: account_create account_id scheme host')
        connection = arg(3)
        if connection is not None:
            Databases().add(account_id,'', connection)
            Databases().test(account_id,'')

    elif action == '_account_database':
        account_id = arg(2)
        if account_id is None:
            print('Вызов: account.create account_id scheme host')
        scheme = arg(3)
        dsn = arg(4)
        account_dir = f'/DOMINO/accounts/{account_id}'
        os.makedirs(account_dir, exist_ok=True)
        info_file = os.path.join(account_dir, 'info.json')
        if os.path.isfile(info_file):
            with open(info_file) as f:
                info = json.load(f)
        else:
            info = {}
        info['company'] = account_id
        database = {'scheme' : scheme.upper(), 'host' : dsn}
        info['database'] = database
        with open(info_file, 'w') as f:
            json.dump(info, f)

    elif action == 'account_config':
        ACCOUNT.config(arg(2), arg(3))
    elif action == 'config':
        CONFIG.config(arg(2), arg(3), arg(4))

    elif action == '--on_install':
        on_install('domino', version)

    #elif action == 'databases':
    #    Databases().print()

    elif action == 'add_database':
        a = arg(2) 
        if a is None:
            sys.exit()
        if a.find('.') != -1:
            account_id, id = a.split('.')
        else:
            id = ''
            account_id = a
        try:
            Databases().add(account_id, id, arg(3))
        except BaseException as ex:
            print(ex)

    elif action == 'remove_database':
        a = arg(2) 
        if a is None:
            sys.exit()
        if a.find('.') != -1:
            account_id, id = a.split('.')
        else:
            id = ''
            account_id = a
        try:
            Databases().remove(account_id, id)
        except BaseException as ex:
            print(ex)

    elif action == 'test_database':
        database = Database.parse(arg(2))
        if database is None:
            print('Не правильно заданы параметры БД')
        else:
            revision = database.get_revision()
            if revision is None:
                print('База данных недоступна')
            else:
                print(f'База данных доступна и имеет версию {revision}')
                
    elif action == 'databases_list':
        host = arg(2) 
        pwd = arg(3) 
        owners = Databases.find(host, pwd)
        print(" ".join(owners))

    elif action == 'help' and arg(2) is not None:
        command = arg(2)
        program = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli', command + ".py")
        if os.path.exists(program):
            command = f'python3.6 {program} --help'
            os.system(command)
    else:
        program = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli', action + ".py")
        if os.path.exists(program):
            args = " ".join(arglist(2))
            command = f'python3.6 {program} {args}'
            print_comment(command)
            os.system(command)
        else:
            print_comment(program)
            print(f'Неизвестная команда "{action}"')

