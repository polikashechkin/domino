import os, sys, datetime, sqlite3, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from domino.core import log, DOMINO_ROOT, Version, IS_WINDOWS, IS_LINUX
from domino.account import find_account_id, Account
from domino.jobs import Proc

from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning
console = Console()

def help():
    print('domino on_activate <module_id> <version> [<account_id>] : Выполнить действия при активации модуля') 

def on_activate_module(module_id, version, account_id):
        info_json = os.path.join(DOMINO_ROOT, 'accounts', account_id, 'info.json')
        if os.path.isfile(info_json):
            with open(info_json) as f:
                info = json.load(f)
            modules = info.get('products')
            if modules:
                if module_id == 'login':
                    console.run(module_id, 'active', 'on_activate', [account_id])
                else:
                    for module_info in modules:
                        id = module_info.get('id')
                        if id and id == module_id:
                            console.run(module_id, version, 'on_activate', [account_id])

def on_activate(module_id, version, account_id):
    print(f'on_activate({module_id}, {version}, {account_id if account_id else "*"} )')
    if account_id:
        on_activate_module(module_id, version, account_id)
    else:
        accounts = os.path.join(DOMINO_ROOT, 'accounts')
        for account_id in os.listdir(accounts):
            on_activate_module(module_id, version, account_id)

if __name__ == "__main__":
    module_id = console.arg(1)
    version = Version.parse(console.arg(2))
    account_query = console.arg(3)
    if account_query:
        account_id = find_account_id(account_query)
        if not account_id:
            print(f'Не надена учетная запись {account_query}')
            sys.exit()
    else:
        account_id = None
    # ------------------------------
    if version is None:
        folder = os.path.join(DOMINO_ROOT, 'products', module_id)
        for version_id in os.listdir(folder):
            _version = Version.parse(version_id)
            if _version:
                if version is None or version < _version:
                    version = _version
    # ------------------------------
    if not module_id or not version:
        help()
        sys.exit(1)

    on_activate(module_id, version, account_id)
