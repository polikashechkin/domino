import flask, sqlite3, json, sys
from domino.page import Page
from domino.core import log
from domino.server import Server
from domino.account import Account, find_account, ACCOUNTS_DB, Dept
from domino.databases import Databases, Database

def open(page):
    page.application['navbar'](page)

    title = page.title(f'Модули')
    title.text_block().href('УСТАНОВИТЬ', '/pages/install')

    config = Server.get_config()

    modules = page.table('modules')
    modules.column().text('ID')
    modules.column().text('Тип')
    modules.column().text('Активная версия')
    modules.column().text('Наименование')
    for product_id in sorted(Server.get_products()):
        r = modules.row(product_id)
        version = config.get_version(product_id)
        info = Server.get_version_info(product_id, version)
        if version is None or info is None:
            continue
        r.text(product_id)
        run_type = info["run_type"]

        if run_type is None:
            r.text('')
        elif run_type == 'login':
            r.text('Приложение')
        else:
            r.text('')

        versions = len(Server.get_versions(product_id))
        if versions > 1:
            r.text(f'{version} ({versions})')
        else:
            r.text(f'{version}')
        r.text(info.description)
