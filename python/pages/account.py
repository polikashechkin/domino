import flask, sqlite3, json, sys
from domino.page import Page
from domino.core import log
from domino.server import Server
from domino.account import Account, find_account, ACCOUNTS_DB, Dept, AccountConfig
from domino.databases import Databases, Database

class ThePage(Page):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.account_id = self.attribute('account_id')
        self.account = find_account(self.account_id)
        self.param_id = self.attribute('param_id')
        self.databases = Databases()
        self.dept_guid = self.attribute('dept_guid')
        self._connection = None
        self._cursor = None
        self._dept = None
    @property
    def dept(self):
        if self._dept is None:
            self._dept = Dept.get(self.connection, self.account_id, self.dept_guid)
        return self._dept
    @property
    def connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(ACCOUNTS_DB)
        return self._connection
    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self.connection.cursor()
        return self._cursor
    
    @staticmethod
    def print_edit_cell(row, edit_method, params = {}):
        row.onclick(edit_method, params)
        cell = row.cell()
        cell.css('text-right').style('width:6rem')
        cell.button().glif('pen', style='color:lightgray').css('bg-white')\
                .onclick(edit_method, params).small()

    @staticmethod
    def print_accept_or_cancel_cell(row, accept_method, cancel_method, params = {}):
        row.css('shadow table-warning')
        cell = row.cell()
        cell.css('text-right align-middle').style('width:6rem')
        cell.button().glif('save').css('bg-white btn-warning')\
            .onclick(accept_method, params, forms=[row])
        cell.glif(':close').style('margin-left:0.5rem').onclick(cancel_method)

    def get_param_value(self, param_id):
        if param_id == 'alias':
            return self.account.alias
        elif param_id == 'database':
            databases = Databases()
            database = databases.get_database(self.account_id)
            return database.uri if database is not None else ''
        return '?'

    def set_param_value(self, param_id, value):
        if param_id == 'database':
            database = Database.parse(value)
            if database is None:
                self.error(f'Ошибка в формате описания соединения с БД "{value}"')
            else:
                Databases().set_database(database, self.account_id)
                revision = database.get_revision()
                if revision is None:
                    self.error(f'"{database.uri}" НЕДОСТУПНА на данном сервере')
                else:
                    self.message(f'"{database.uri}" доступна и имеет версию "{revision}"')
        elif self.param_id == 'alias':
            self.account.alias = value

    def error(self, msg):
        self.message(msg).style('color:white').css('bg-danger')

    def accept(self):
        value = self.get('value')
        self.set_param_value(self.param_id, value)
        self.params()
            
    def cancel(self):
        self.params()

    def edit(self):
        params = self.table('params')
        value = self.get_param_value(self.param_id)
        p = params.row(self.param_id)
        #.css('shadow table-warning')
        p[0].text(self.get('label'))
        p[1].input(name='value', value=value)
        ThePage.print_accept_or_cancel_cell(p, '.accept', '.cancel', {'param_id': self.param_id})

        #cell = p[2].css('text-right align-middle').style('width:4rem')
        #cell.button().glif('save').css('bg-white btn-warning').onclick('.accept', {'param_id': self.param_id}, forms=[p])
        #cell.glif(':close').style('margin-left:0.5rem').onclick('.cancel')

    @staticmethod
    def param(params, param_id, label, value, editable=False):
        param = params.row(param_id)
        param[0].style('width:20rem').text(label)
        param[1].text(value)
        #param[2].css('text-right').style('width:6rem')
        if editable:
            ThePage.print_edit_cell(param, '.edit', {'param_id': param_id, 'label':label})
            #param.onclick('.edit', {'param_id': param_id, 'label':label})
            #param[2].button().glif('pen').css('bg-white')\
            #    .onclick('.edit', {'param_id': param_id, 'label':label}).small()
        else:
            param.text('')

    def params(self):
        params = self.table('params', hole_update=True)

        ThePage.param(params, 'alias', 'Псевдоним', self.account.alias, editable=True)
        ThePage.param(params, 'description', 'Описание', self.account.description)
        ThePage.param(params, 'password', 'Пароль', self.account.password)

        log = params.row('log')
        log.text('Журнал сообщений')
        log.href('подробнее...', 'pages/log.open')
        log.text('')

        ThePage.param(params, 'database', 'Основная база жанных', self.get_param_value('database'), editable=True)

        depts = params.row('depts')
        depts.text('Зарегистрированных подразделений')
        with sqlite3.connect(ACCOUNTS_DB) as conn:
            count = Dept.count(conn, '''account_id=? and code != '' and code != '.' ''', [self.account_id])
        depts.href(f'{count if count > 0 else "Нет"}', 'pages/depts', {'account_id': self.account_id})
        depts.text('')

        modules = params.row('modules')
        account_config = AccountConfig.load(self.account)
        names = []
        for product in account_config.products:
            try:
                version = product.version
                if version is None or str(version) == 'active':
                    version = Server.get_active_version(product.id)
                info = Server.get_version_info(product.id, version)
                if info is not None:
                    description = info.description
                    if description is not None and description.strip() != '':
                        names.append(description)
                    else:
                        names.append(product.id)
                else:
                    c = AccountConfig.load(self.account)
                    c.remove(product.id)
                    AccountConfig.save(self.account, c)
                    continue
            except:
                names.append(product.id)
        modules.text('Модули')
        modules.href(', '.join(names) if len(names)>0 else 'Нет', 'pages/account_modules', {'account_id':self.account_id})

    def dept_accept(self):
        database_uri = self.get('database_uri')
        database = Database.parse(database_uri)
        if database is None:
            self.error(f'Неправильный формат "{database_uri}"')
        else:
            self.databases.set_database(database, self.account_id, self.dept.guid)
            self.print_dept(self.table('depts'), self.dept)
            self.message('dept_accept')

    def dept_cancel(self):
        self.print_dept(self.table('depts'), self.dept)

    def dept_edit(self):
        self.print_dept(self.table('depts'), self.dept, True)

    def print_dept(self, table, dept, edit=False):
        if dept is None:
            r = table.row()
            r.text('')
            r.text('Неизвестное подразделение')
            return
        r = table.row(dept.guid)
        if dept.is_account_dept:
            r.glif('home')
        else:
            r.text(dept.code)
        r.text(dept.name)
        database = self.databases.get_database(self.account_id, dept.guid)
        database_uri = database.uri if database is not None else ''
        if edit:
            r.input(value=database_uri, name='database_uri')
            ThePage.print_accept_or_cancel_cell(r, '.dept_accept', '.dept_cancel', {'dept_guid':dept.guid})
        else:
            r.text(database_uri)
            ThePage.print_edit_cell(r, '.dept_edit', {'dept_guid':dept.guid})
        
    def open(self):
        self.title(f'{self.account.description} {self.account.id}')
        self.params()
   
        self.header().text('Подразделения')
        t = self.table('depts')
        t.column().text('Код')
        t.column().text('Наименование')
        t.column().text('База данных').style('width:40em;')
        t.column().text('')
        with sqlite3.connect(ACCOUNTS_DB) as conn:
            for dept in Dept.findall(conn, 'account_id=?', [self.account_id]):
                if dept.code == '':
                    continue
                self.print_dept(t, dept)
