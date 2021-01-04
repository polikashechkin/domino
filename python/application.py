#< import 
from flask import Flask, request
import os, sys, sqlite3
import json, pickle
import requests                 
import datetime, arrow
from domino.account import find_account, find_account_id, DEPTS_DB, Device
from domino.core import log, Version
from domino.server import Server
#from domino.request import DominoRequest
from domino.products import Product
from domino.metrics import Metric, LOCATION, MOBILE
from domino.application import Application, Status
import xml.etree.ElementTree as ET
      
from domino.account_db import AccountDb

ACCOUNT_DB = AccountDb.Pool()
#> 
# os, sys, Стандартные модули PYTHON / os, sys, datetime, arrow, sqlite3,  pydwdwd, cx_Orcale, "name", "description" "href"
# domino.ROOT ""  
                                                                        
def LOG_DB(account_id):
    return f'/DOMINO/accounts/{account_id}/data/log.db'
 
account_requests = set()
      
def log_connect(account_id):
    db = LOG_DB(account_id)
    if account_id not in account_requests:
        account_requests.add(account_id)
        os.makedirs(os.path.dirname(db), exist_ok=True)
        with sqlite3.connect(db) as conn: 
            conn.executescript('''
            create table if not exists log 
            (
                account_id not null,
                date not null,
                level, 
                product_id,
                info 
            );
            ''')
   
    return sqlite3.connect(db)
                                                                     
app = Flask(__name__)
application = Application(os.path.abspath(__file__), framework='MDL')

@app.route('/about')
def _about():
    return 'domino'
                                                                                                             
def navbar(page): 
    nav = page.navbar()
    nav.header(f'{application.hostname}', 'pages/start_page')
    #nav.item('Регистрация', 'pages/about')
    #nav.item('Учетнные записи', 'pages/accounts.open')
    #accounts = nav.group('Учетнные записи')
    #accounts.item('Учетнные записи (полный список)', 'pages/accounts')
    #accounts.item('Учетнные записи имеющие псевдоним', 'pages/accounts.with_alias')
    #nav.item('Модули', 'pages/modules')
    # pages
    #   page job from wdwddw:/domino/job_page
    #   page.grants = Grants(page.acount_id, 'discount', page.user_id)
    nav.item('Процедуры', 'procs')
    nav.item('Задачи', 'jobs')
    nav.item('Базы данных', 'pages/databases')
                                            
application['navbar'] = navbar               
                
def SUCCESS(params = {}): 
    return Status.success(params).json()
               
def ERROR(msg, params = {}):
    return Status.error(msg, params).json()
      
def EXCEPTION(msg, params = {}):
    return Status.exception(msg, params).json()
                    
# -------------------------------------------
@app.route('/server.info')
def get_server_info():
    try:
        return pickle.dumps(Server.info())
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', f'500 {ex}'

# -------------------------------------------
@app.route('/server.account_info')
def get_account_info():
    try:
        account = find_account(request.args.get('account_id'))
        return pickle.dumps(account.info)
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', f'500 {ex}'

# -------------------------------------------
@app.route('/write_log')
def write_log():  
    '''
    Записть в журнаял произвольных сообщений для последующего анализа
    Вызов GET
        <сервер>/domino/active/python/write_log?[параметры]
    Параметры
        account_id - Учетная запись (обязательно)
        data - дата время в формате ISO (YYYY-MM-DD HH:MM:SS)
        product_id - идентификатор продукта (модуля)
        прочие параметры записываются в log в том виде, как пришли
    Возврат Status в формате JSON 
    '''  
    try:
        account_id = None
        level = ''
        product_id = ''
        date = f'{datetime.datetime.now()}'
        info = {}
        for key, value in request.args.items():
            if key == 'account_id':
                account_id = value
            elif key == 'level':
                level = value
            elif key == 'product_id':
                product_id = value
            elif key == 'date':
                date = value
            else:
                info[key] = value
        account = find_account(account_id)
        if account is None:
            return Status.error(f'Учетная запись "{account_id}" не зарегитрирована на данном сервере').json()
        conn = log_connect(account_id)
        with conn:
            conn.execute('''
            insert into log (account_id, date, level, product_id, info)
            values(?,?,?,?,?)
            ''', [account_id, date, level, product_id, json.dumps(info, ensure_ascii=False)])
        #return 'hello1'
        return Status.success().json()
    except BaseException as ex:
        log.exception(request.url)
        #return f'error '
        return Status.exception(f'{ex}').json()
     
# -------------------------------------------
@app.route('/get_product_info')
def get_product_info():
    '''
    Проверка наличие функцонирующего продукта на данном сервере.
    Продукт должет быть активирован для определенной Учетной Записи
    Вызов (GET)
        <сервер>/domino/active/python/get_product_info
    Параметры
        product_id идетификатор продукта (модуля)
        account_id идентфикаторв учетной записи
    Возврат (json, UTF-8)
        Если активнй продукт не найден 
        {"status":"error", "message":"Описание причины"}
        Если есть такой, то
        {"status":"success", "version":"Версия продукта", "info" : {..} }
        В параметре инфо передается копия файла info.json расположнного в
        директории версии продукта
    '''
    try:
        product_id = request.args.get('product_id')
        if product_id is None:
            return ERROR(f"Не задан продукт")
        version = Server.get_active_version(product_id)
        version_info = Server.get_version_info(product_id, version)
        if version is None:
            return ERROR(f'Продукт(модуль) "{product_id}" не доступен на данном сервере')
        account_id = request.args.get('account_id')
        account = find_account(account_id)
        if account is None:
            return ERROR(f'Учетная запись "{account_id}" не зарегистрирована на данном сервере')
        return SUCCESS({"version":str(version), "info" : version_info.js})
    except BaseException as ex:
        log.exception(request.url)
        return EXCEPTION(f'{ex}')

# -------------------------------------------
@app.route('/get_product_status_xml')
def get_product_status_xml():
    '''
    Проверка наличие функцонирующего продукта (модуля) на данном сервере.
    Продукт должет быть активирован для определенной Учетной Записи
    Вызов (GET)
        <сервер>/domino/active/python/get_product_status_xml
    Параметры
        product_id идетификатор продукта (модуля)
    Возврат (xml, UTF-8)
        Если активнй продукт не найден 
        <STATUS status='error'"message":"Описание причины"/>
        Если есть такой, то
        <STATUS status="success" version="Версия продукта"/>
    '''
    try:
        product_id = request.args.get('product_id')
        if product_id is None:
            return Status.error(f"Не задан продукт").xml()
        version = Server.get_active_version(product_id)
        version_info = Server.get_version_info(product_id, version)
        if version is None:
            return Status.error(f'Продукт(модуль) "{product_id}" не доступен на данном сервере').xml()
        return Status.success({"version":str(version)}).xml()
    except BaseException as ex:
        log.exception(request.url)
        return Status.exception(f'{ex}').xml()
                  
# -------------------------------------------
@app.route('/get_depts')
def get_depts():
    '''
    Возвращает список подразделений, рарегистрированных на данном
    сервере (синхонихированных из личного кабинета). Т.е. основные (лицензионные)
    параметры задаются в личном каюинете, а дополнительные задаются непосредственно 
    на сервере
    [
        {"guid" : guid, "name":name, "code": code},
    ]
    При осуществлении вызовов, следует использовать БД
    account_id.guid заведенные на сервере
    Команда:
    domino add_database <account_id>.<guid> <user@dsn>

    Когда делается LOGIN в sk заносится не только account_id. но и guid подразделения
    В процессе обработки запроста - база данных получается после вызова:
    Databases().ac..(accouny_id, guid)
    '''
    depts = []
    try:
        account = find_account(request.args.get('account_id'))
        if account is not None:
            with sqlite3.connect(DEPTS_DB) as conn:
                cur = conn.cursor()
                cur.execute('''
                select guid, name, code from depts where account_id=?
                ''', [account.id])
                for guid, name, code in cur:
                    depts.append({'account_id':account.id, 'guid':guid, 'name':name, 'code': code})
    except:
        log.exception(request.url)

    return json.dumps(depts)
  
# -------------------------------------------
@app.route('/check_workplace')
def check_workplace():
    '''
    Проверка доступности устройства, в зависимости от политики безопастности,
    принятой в организации.
    Устройство может быть доступно или нет. Если устройствно не доступно, то
    работать с ним нельзя, следует уведомить пользователя и не работать
    Заодно, это информация о статусе устройства (жив - нет) и возможно о некоторых
    характеристиках устройства
    Параметры:
    account_id : идентификатор учетной записи
    type : устройства могут быть разных типов:
        MOBLE - смартфонон
        COMPUTER - компьютер
        SERVER - сервер
        FSRAR - ФСРАР
        FR_REGNO - Фискальный регистратор
    id : Уникальный ключ (ижентификатор) устройства
    Возврат json структура:
    {"status" : "...", "message":"..."}
    status : если статуса нет или это "success". то все хорошо
             если "error", то в поле message сообщение об ошибке 
    Прочие параметры вызова интерпретируются, как характеристики устройства.
    Стандартными являются:
    name - имя (наименование)
    descriptiion - произвольное описание
    dept - код подразделения, к ктоторому данное устройство привязано в настоящий момент
   
    '''
    try:
        # Начальные значения
        ACCOUNT_ID = None
        TYPE_ID = None
        ID = None
        NAME = None
        DESCRIPTION = None
        INFO = {}

        # Определение параметров
        for arg, value in request.args.items():
            if arg == 'account_id':
                ACCOUNT_ID = value
            elif arg == 'type':
                TYPE_ID = value
            elif arg == 'id':
                ID = value
            elif arg == 'name':
                NAME = value
            elif arg == 'description':
                DESCRIPTION = value
            else:
                INFO[arg] = value
         
        # Обработка параметров    
        account = find_account(ACCOUNT_ID)
        if account is None:
            return ERROR(f'Учетная запись "{ACCOUNT_ID}" не зарегистрирована на данном сервере')
        if TYPE_ID is None:
            return Status.error(f'Не определен параметр "type"')
        metric = Metric.get(TYPE_ID)
        if metric is None :
            return ERROR(f'Неизвестный тип "{TYPE_ID}"')
        TYPE = metric.id
        if ID is None:
            return ERROR(f'Не задан идентификатор объекта')
        KEY = ID
  
        # Проверка статуса устройства на текущем сервере
        with sqlite3.connect(DEPTS_DB) as conn:
            cur = conn.cursor()
            device = Device.get_by_key(cur, account.id, TYPE, ID)
            if device is None:
                device = Device.create(cur, account.id, TYPE, ID)
            if NAME is not None:
                device.name = NAME
            if DESCRIPTION is not None:
                device.description = DESCRIPTION
            for key, value in INFO:
                device.info[key] = value
            device.update(cur)

        #if Server.unregister:
        #   return Status.error(f'Сервер не зарегистирован')
        #if not Server.root_server:
        #    reg = Server.reg_server()
        #    reg.get_status('check_workplace', request.args)

        if device.status < 0:
            return Status.error(f'Использование запрещено', {'device_status':f'{device.status}'}).json()
        else:
            return Status.success({'device_status':f'{device.status}'}).json()
    except BaseException as ex:
        log.exception(request.url)
        return Status.exception(f'{ex}').json()
  
# -------------------------------------------
@app.route('/check_license')
def check_license():
    #log.debug(request.url)
    '''
    Проверяет наличие лицензий дял продкта на какой либо объект лицензирования
    Если лицензий нет, то создается временная лицензия
    Параметры
        account_id : Учетная записть
        product_id : Идентификатор продукта (M_ASSIST, RETAIL_POS ...)
        type : тип лицензионного объекта (LOCATION, MOBILE, COMPUTER ...)
        id : Идентификатор лицензируемого объекта
    Возвращет структуру:
        {"status" : "...", "message":"...", "exp_date":"YYYY-MM-DD" }
    Если с лицензией все хорошо, то выдвется status = "success" и задается exp_date,
    если плохо, то выдается status="error" и message=сообщение об ошибке
    '''
    try:
        account_id = request.args.get('account_id')
        account = find_account(account_id)
        if account is None:
            return ERROR(f'Учетная запись (account_id) "{account_id}" не зарегистрирована на данном сервере')
    
        product_id = request.args.get('product_id')
        product = Product.get(product_id)
        if product is None:
            return ERROR(f'Неизвестный продукт (product_id) "{product_id}"')

        type = request.args.get('type')
        metric = Metric.get(type)
        if metric is None:
            return ERROR(f'Неизвестный тип "{type}"')

        id = request.args.get('id') 
        if id is None:
            return ERROR(f'Не задан идентификатор объекта')
        
        dept = None
        if metric == LOCATION:
            dept = account.find_dept(id)
            if dept is None:
                return ERROR(f'Подразделение "{id}" не зарегистрировано на данном сервере')
            if not dept.enabled:
                return ERROR(f'Подразделение "{id}" заблокировано для использования')
            id = dept.guid

        ac_domino_ru = Server.get_config().ac_domino_ru

        params = {"account_id" : account.id, "product_id":product.id, "type":metric.id, "id": id}
        r = requests.get(f'https://{ac_domino_ru}/ls/check_trial',params = params)
        if r.status_code == 200:
            expired = False 
            date = ''
            if r.text.strip() == '': 
                expired = True
            else:
                date = arrow.get(r.text).date()
                if date < arrow.get().date():
                    expired = True
            if expired:
                dept_code = dept.code if dept is not None else ''
                return ERROR(f'Использование продукта "{product.name}" для подразделения "{dept_code}" истекло {date}', {'exp_date':str(date)})
            else:
                return SUCCESS({"exp_date" : r.text})
        else:
            return EXCEPTION(f'{r.text}', {'url':r.url, 'status_code':r.status_code})
    except BaseException as ex:
        log.exception(request.url)
        return EXCEPTION(f'{ex}')

# -------------------------------------------
@app.route('/get_version')
def get_version():
    product = request.args.get('product')
    if product is None:
        return f'Unknown product "{product}"', '400 Unknown product "{product}"'
    latest = Server.get_latest_version(product)
    if latest is None:
        return f'Latest version of "{product}"" not found', '404 Latest version of "{product}" not found'
    else:
        return f'{latest}'
   
#< /pages/start_page 
import pages.start_page
@app.route('/pages/start_page', methods=['GET','POST'])
def _pages_start_page():
    try:
        page = pages.start_page.Page(application, request)
        return page.make_response()
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
@app.route('/pages/start_page.<fn>', methods=['GET','POST'])
def _pages_start_page_fn(fn):
    try:
        page = pages.start_page.Page(application, request)
        return page.make_response(fn)
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
#>
             
import pages.databases
@app.route('/pages/databases', methods=['GET','POST'])
def _pages_databases():
    return application.response(request, pages.databases.Page, None, [ACCOUNT_DB])
@app.route('/pages/databases.<fn>', methods=['GET','POST'])
def _pages_databases_fn(fn):
    return application.response(request, pages.databases.Page, fn, [ACCOUNT_DB])

import pages.database
@app.route('/pages/database', methods=['GET','POST'])
def _pages_database():
    return application.response(request, pages.database.Page, None , [ACCOUNT_DB])
@app.route('/pages/database.<fn>', methods=['GET','POST'])
def _pages_database_fn(fn):
    return application.response(request, pages.database.Page, fn , [ACCOUNT_DB])

# ProcsPage -------------------------------------------
from domino.jobs_pages import ProcsPage
@app.route('/procs', methods=['GET','POST'])
def procs():
    return ProcsPage(application, request).make_response()
@app.route('/procs.<fn>', methods=['GET','POST'])
def procs_fn(fn):
    try:
        return ProcsPage(application, request).make_response(fn)
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
        
# JobsPage -------------------------------------------
from domino.jobs_pages import JobsPage
@app.route('/jobs', methods=['GET','POST'])
def jobs():
    try:
        return JobsPage(application, request).make_response()
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
@app.route('/jobs.<fn>', methods=['GET','POST'])
def jobs_fn(fn):
    try:
        return JobsPage(application, request).make_response(fn)
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
  
#< JobPage 
import domino.jobs_pages 
@app.route('/download_job_file', methods=['GET','POST'])
def download_job_file():
    return domino.jobs_pages.download_job_file(request)
from domino.jobs_pages import JobPage
@app.route('/job', methods=['GET','POST'])
def job():
    try:
        return JobPage(application, request).make_response()
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
@app.route('/job.<fn>', methods=['GET','POST'])
def job_fn(fn):
    try:
        return JobPage(application, request).make_response(fn)
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}', 500
#>
        
