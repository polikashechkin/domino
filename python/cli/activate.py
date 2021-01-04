import os, sys, datetime, sqlite3, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from domino.core import log, DOMINO_ROOT, Version, IS_WINDOWS, IS_LINUX
from domino.account import find_account_id
from domino.jobs import Proc

from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning

def help():
    print('domino activate <module> <version>  : Активировать версию модуля') 

def activate(module_id, version):
    # устанавливаем symlinc (active=>version) 
    active_folder = os.path.join(DOMINO_ROOT, 'products', module_id, 'active')
    module_folder = os.path.join(DOMINO_ROOT, 'products', module_id, f'{version}')
    application_py = os.path.join(module_folder, 'python', 'application.py')
    if not os.path.isfile(application_py):
        print(application_py)
        print(f'НЕ НАЙДЕН МОДУЛЬ {module_id} {version}')
        return
    if os.path.exists(active_folder):
        os.unlink(active_folder)
    os.symlink(module_folder, active_folder)
    print(f'Установлена символическая ссылка {module_folder} => {active_folder}')
    # устанавливаем (обновляем) uwsgi socket
    if IS_LINUX:
        vassal_ini = os.path.join(DOMINO_ROOT, 'uwsgi', 'vassals', f'{module_id}.active.ini')
        with open(vassal_ini, 'w') as f:
            f.write(f'[uwsgi]\n')
            f.write(f'chdir = /DOMINO/products/{module_id}/{version}/python\n')
            f.write(f'socket = /DOMINO/uwsgi/sockets/{module_id}.active.sock\n')
            f.write(f'touch-reload = {application_py}\n')
            f.write(f'python-autoreload=1\n')
            f.write(f'harakiri = 60\n')
        print(f'Создан/обновлен uwsgi vassal "{vassal_ini}')

if __name__ == "__main__":
    if arg(1) is not None and arg(1) == '--help':
        help()
        sys.exit()
    module_id = arg(1)
    version = Version.parse(arg(2))
    if module_id is None or version is None:
        help()
    activate(module_id, version)
