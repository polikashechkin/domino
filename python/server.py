import os, json, pickle, sqlite3

from domino.core import log, Version
from domino.account import find_account, DEPTS_DB, Dept
from domino.server import Server
#from domino.application import SUCCESS

class Status:
    def __init__(self, status):
        self.js = {'status':status}
    @property
    def success(self):
        return self.js['status'] == 'success'

    def get(self, propname):
        return self.js.get(propname)

def SUCCESS():
    return pickle.dumps(Status('success'))

def ERROR(message):
    status = Status('error')
    status.js['message'] = message
    return pickle.dumps(status)
    
def about(request):
    return "server"

def info(request):
    try:
        return pickle.dumps(Server.info())
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', f'500 {ex}'

def account_info(request): 
    account = find_account(request.args.get('account_id'))
    return pickle.dumps(account.info)

def dept(request):
    account = find_account(request.args.get('account_id'))
    dept_id = request.args.get('dept_id')
    return pickle.dumps(account.find_dept(dept_id))

def reg_server(request):
    account = find_account(request.args.get('account_id'))
    dept_id = request.args.get('dept_id')
    dept = account.find_dept(dept_id)
    dept.info['server_guid'] = request.args.get('server_guid')
    with sqlite3.connect(DEPTS_DB) as conn:
        Dept.update(conn, dept)
    return SUCCESS()

def depts(request):
    account = find_account(request.args.get('account_id'))
    with sqlite3.connect(DEPTS_DB) as conn:
        depts = Dept.findall(conn, "account_id=? and name != '' ", [account.id])
    return pickle.dumps(depts)

def reg_database(request):
    account_id = request.args.get('account_id')
    account = find_account(account_id)
    if account is None:
        return ERROR(f'Учетная записть {account_id} не найдена')
    dept_id = request.args.get('dept_id')
    dept = account.find_dept(dept_id)
    if dept is None:
        return ERROR(f'Пожразделение {dept_id} не найдено')
        
    database_uri = request.args.get('database')
    dept.set_param(Dept.DATABASE_URI, database_uri)
    with sqlite3.connect(DEPTS_DB) as conn:
        Dept.update(conn, dept)
    return SUCCESS()
    
