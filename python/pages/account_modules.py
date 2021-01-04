import flask, sqlite3, json, sys
from domino.page import Page
from domino.core import log
from domino.server import Server
from domino.account import Account, find_account, ACCOUNTS_DB, Dept, AccountConfig
from domino.databases import Databases, Database

def button_check(cell, checked, onchange = [], params = {}, forms = []):
    if checked:
        cell.button().glif('check').small().css('bg-white text-success')\
            .onclick(onchange[0], params, forms)
    else:
        cell.button().small().css('bg-white disabled').glif('check', style='color:rgb(220,220,210)')\
            .onclick(onchange[1], params, forms)

def add_row(table, product_id, account_config):
    #if account_config.get(product_id) is None:
    #    row[0].button().glif('check').small().css('bg-white text-success')\
    #        .on_click('.add', {'product_id':product_id})
    #else:
    #    row[0].button().small().css('bg-white disabled').glif('check', style='color:rgb(220,220,210)')\
    #        .on_click('.remove', {'product_id':product_id})

    exists = account_config.get(product_id) is not None

    version = '?'
    description = '?'
    
    if exists:
        try:
            version = Server.get_active_version(product_id)
            info = Server.get_version_info(product_id, version)
            description = info.description
        except:
            pass
    else:
        version = Server.get_active_version(product_id)
        if version is None:
            return 
        info = Server.get_version_info(product_id, version)
        if info is None:
            return 
        run_type = info['run_type']
        if run_type is None or run_type != 'login':
            return
        description = info.description

    row = table.row(product_id)
    button_check(row[0], exists, ['.remove', '.add'], {'product_id':product_id})
    row.text(product_id)
    row.text(description)
    row.text(version)
    #if account_config.get(product_id) is None:
    #    add_button = row.button('Добавить').css('btn-primary').small()
    #    add_button.onclick('.add', {'product_id':product_id})
    #else:
    #    remove_button = row.button('Удалить').css('btn-danger').small()
    #    remove_button.onclick('.remove', {'product_id':product_id})

def add(page):
    account_id = page.attribute('account_id')
    product_id = page.get('product_id')
    account = find_account(account_id)
    account_config = AccountConfig.load(account)
    account_config.add(product_id, 'active')
    AccountConfig.save(account_config, account)
    modules = page.table('modules')
    add_row(modules, product_id, account_config)
    return page.update()

def remove(page):
    account_id = page.attribute('account_id')
    product_id = page.get('product_id')
    account = find_account(account_id)
    account_config = AccountConfig.load(account)
    account_config.remove(product_id)
    AccountConfig.save(account_config, account)
    modules = page.table('modules')
    add_row(modules, product_id, account_config)
    return page.update()

def open(page):
    page.application['navbar'](page)
    account_id = page.attribute('account_id')
    account = find_account(account_id)
    account_config = AccountConfig.load(account)

    page.title(f'Модули {account_id}')

    #page.header().text('Модули')
    comment = page.text_block('modules_comment')
    comment.text('Список установленных на сервере модулей типа "Приложение". ')
    #comment.text('Это те модули, которые доступны пользователям при входе в систему. ')
    #comment.text('Для расширения списка следует перейти на страницу ')
    #comment.href('Добавление модуля', 'pages/account_modules')

    modules = page.table('modules')
    modules.column().text('')
    modules.column().text('ID')
    modules.column().text('Описание')
    modules.column().text('Версия')
    #modules.column().text('').style('width:1em')

    for product_id in Server.get_products():
        add_row(modules, product_id, account_config)
