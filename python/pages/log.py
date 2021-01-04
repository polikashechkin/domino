import flask, sqlite3, json, sys
from domino.page import Page
from domino.core import log
from domino.account import Account
from application import log_connect

def open(page):
    page.application['navbar'](page)
    account_id = page.attribute('account_id')
    page.title(f'Журнал сообщений')

    table = page.table('log')
    table.column().text('#')
    table.column().text('Дата')
    table.column().text('Уровень')
    table.column().text('Продукт')
    table.column().text('Сообщение')

    conn = log_connect(account_id)
    cur = conn.cursor()
    cur.execute(''' 
        select rowid, date, level, product_id, info from log order by rowid desc
    ''')
    for rowid, date, level, product_id, info in cur:
        row = table.row(rowid)
        row.fields(rowid, date, level, product_id, info)
        
        

