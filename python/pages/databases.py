import os, json, sys
from pages._base import Page as BasePage
from pages._base import Button
from domino.core import log
from tables.account_db.database import Database
import cx_Oracle
 
class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)

    def check_database(self):
        account_id = self.get('account_id')
        database_id = self.get('database_id')
        database = self.account_db.query(Database).get((account_id, database_id))
        try:
            conn = cx_Oracle.connect(user = database.scheme, password = database.scheme, dsn = database.dsn, encoding = "UTF-8", nencoding = "UTF-8") 
            conn.close()
            connection = True
        except BaseException as ex:
            self.error(f'{ex}')
            connection=False

        row = self.Row('databases', f'{account_id}:{database_id}')
        self.print_row(row, database, connection)

    def print_row(self, row, database, connection = None):
        row.text(database.account_id)
        row.text(database.database_id)
        row.href(f'{database.user_name}@{database.dsn}', 'pages/database', {'account_id':database.account_id, 'database_id':database.database_id})
        cell = row.cell(align='right')
        if connection is None:
            Button(cell, 'Проверить').onclick('.check_database', {'account_id':database.account_id, 'database_id':database.database_id})
        elif connection :
            Button(cell, 'Доступна', style='color:white; background-color:green')
        else:
            Button(cell, 'Не доступна', style='color:white; background-color:red')

    def __call__(self):
        self.title(f'Базы данных')

        databases = self.table('databases')
        databases.column().text('Учетная запись')
        databases.column().text('Идентификатор')
        databases.column().text('Описание')
        databases.column()

        for database in self.account_db.query(Database)\
                .filter(Database.account_id != '')\
                .order_by(Database.account_id, Database.database_id):
            row = databases.row(f'{database.account_id}:{database.database_id}')
            self.print_row(row, database)
