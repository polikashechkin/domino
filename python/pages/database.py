import flask, sqlite3, json, sys
from domino.page import Page as BasePage
from domino.core import log
from domino.server import Server
from tables.account_db.database import Database
import cx_Oracle
#from domino.account import Account, find_account, ACCOUNTS_DB, Dept, AccountConfig
#from domino.databases import Databases, Database, DATABASES_DB

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)

    def __call__(self):
        account_id = self.get('account_id')
        database_id = self.get('database_id')
        database = self.account_db.query(Database).get((account_id, database_id))

        self.title(f'{database.user_name}@{database.dsn}')

        params = self.table('params')
        r = params.row()
        r.text('Учетная запись')
        r.text(database.account_id)

        r = params.row()
        r.text('Идентификатор базы данных')
        r.text(database.database_id)

        r = params.row()
        r.text('Строка связи')
        r.text(database.url)

        try:
            conn = cx_Oracle.connect(user = database.scheme, password = database.scheme, dsn = database.dsn, encoding = "UTF-8", nencoding = "UTF-8") 
            p = self.text_block()
            p.header('ДОСТУПНА')
        except BaseException as ex:
            self.error(f'{ex}')
            p = self.text_block().style('color:red;')
            p.header('НЕДОСТУПНА')
