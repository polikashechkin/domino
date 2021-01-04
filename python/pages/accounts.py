import flask, sqlite3, json, sys
from domino.page import Filter
from domino.core import log
from domino.account import Account

class PageContext:
	def __init__(self, page):
		self.page = page
		self.mode = page.attribute('mode')
		self.filter = page.attribute('filter')
'''
def with_alias(page):
    page.application['navbar'](page)
    page.title(f'Учетные записи')

    table = page.table('accounts')
    for account in sorted(Account.findall(), key = lambda a : a.description if a.description is not None else '') :
        if account.alias is not None and account.alias.strip() != '':
            row = table.row(account.id)
            row.href(account.id, 'pages/account', {'account_id':account.id})
            row.text(account.alias)
            row.text(account.description if account.description is not None else '')
'''

def accounts(ctx):
	filter = Filter(ctx.filter)
	table = ctx.page.table('accounts', hole_update=True)
	table.column().text('ID')
	table.column().text('Псевдоним')
	table.column().text('Описание')
	for account in sorted(Account.findall(), key = lambda a : a.description if a.description is not None else '') :
		if ctx.mode == 'alias':
			if account.alias is None or account.alias.strip() == '':
				continue
		if not filter.match(account.id, account.alias, account.description):
			continue
		row = table.row(account.id)
		row.href(account.id, 'pages/account', {'account_id':account.id})
		row.text(account.alias if account.alias is not None else '')
		row.text(account.description if account.description is not None else '')

def get(page):
	ctx = PageContext(page)
	accounts(ctx)

def open(page):
	page.application['navbar'](page)
	ctx = PageContext(page)

	page.title(f'Учетные записи')
	toolbar = page.toolbar('toolbar')
	modes = toolbar.item().select(name='mode', value=ctx.mode).onchange('.get', forms=[toolbar]).small()
	modes.option('all', 'Все учетные записи')
	modes.option('alias', 'Учетные записи, имеющие псевдоним')

	filter_box = toolbar.item().css('ml-auto').input_group().small()
	filter_box.input(name='filter', value=ctx.filter)
	filter_box.button().glif('search').onclick('.get', forms=[toolbar])

	accounts(ctx)
