import os, sys, sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domino.cli import Console, print_comment, arg, print_error, print_header, print_warning
from domino.databases.oracle import Databases, Database
from domino.log import log
from domino.server import Server, GUID
from domino.account import Account, DEPTS_DB, find_account, Dept, MASTER_DEPT_CODE, AccountConfig

if __name__ == "__main__":
    c = Console()
    accounts = Account.findall()
    for account in accounts:
        account_id = account.id
        alias = account.alias
        if alias is None:
            alias = ''
        description = account.description
        if alias.strip() == '':
            id = f'{account_id}'
        else:
            id = f'{account_id}({alias}) '
        msg = f'{id:20}\t{description}'
        print(msg)

