import flask, sqlite3, json, sys
from domino.core import log
from domino.server import Server
from domino.account import Account, find_account, ACCOUNTS_DB, Dept
from domino.globalstore import GlobalStore
from domino.jobs import query_job, start_job

def install(page):
    product_id = page.get('product_id')
    job_id = query_job('domino', 'install', [product_id])
    start_job(job_id)
    page.message(f'Запущена установка "{product_id}" ({job_id})')
    #page.message(f'Запущена установка "{product_id}"')
    return page.update()

def open(page):
    page.application['navbar'](page)
    page.title(f'Установка')

    modules = page.table('modules')
    #modules.column()
    modules.column().text('Модуль')
    modules.column().text('Версия')
    modules.column().text('Активная версия')
    modules.column().style('width:1em')
    gs = GlobalStore()
    for name in gs.listdir('products'):
        version = gs.get_latest_version(name)
        if version is None:
            continue
        row = modules.row(name)
        active_version = Server.get_active_version(name)
        row.text(name)
        row.text(f'{version}')
        row.text(f'{active_version if active_version is not None else ""}')
        row.button_group().button('Установить').action('pages/install.install', {'product_id':name}).css('btn-primary').small()


