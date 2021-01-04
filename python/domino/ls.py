import os, io, re, datetime, json
import xml.etree.cElementTree as ET
from Crypto.PublicKey import RSA
from glob import glob

from domino.core import log
from domino.metrics import Metric, NONE, FSRAR, INN, NETHASP, MEMOHASP
from domino.products import Product, UNKNOWN, DOMINO, RETAIL_ALCO, RETAIL_STORE_KZ

import sqlite3

ACCOUNTS = '/DOMINO/accounts'

#TRIAL_PERIOD = datetime.timedelta(days=30)    

def TRIAL_DATE():
    today = datetime.date.today()
    if today.month > 10:
        trial_date = datetime.date(today.year + 1, today.month - 10, 1)
    else:
        trial_date = datetime.date(today.year, today.month + 2, 1)
    return trial_date
        

def FINAL_FILENAME(account_id):  return account_id + ".final.sft"
def ORIGINAL_FILENAME(account_id):  return account_id + ".sft"
def TRIAL_STORAGE(account_id):  return os.path.join(ACCOUNTS, account_id, "sft", "trials")
def LICENSES_DB(account_id): return os.path.join(ACCOUNTS, account_id, "data", "licenses.db")

#public_key_file = "/DOMINO/resources/sft/public.cer"
public_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public.cer")
private_key_file = "/DOMINO/resources/sft/private.cer"

public_key_value = open(public_key_file, 'rb').read()
private_key_value = open(private_key_file, 'rb').read()

def from_domino_date(text):
   try:
      p = re.findall('([0-9]+)[/. ;]', text + ';')
      day = int(p[0])
      month = int(p[1])
      year = int(p[2])
      return datetime.date(year, month, day)
   except:
      return datetime.date.max

def to_domino_date(date):
    return date.strftime("%d/%m/%Y")

class CfgNode:
    @staticmethod
    def create(metric, key, product, exp_date, trial = False, client_name = None):
        node = ET.fromstring('<CFG>\n</CFG>')
        if trial:
            ET.SubElement(node, 'TRIAL').text = datetime.date.today().__str__()
        ET.SubElement(node, 'CFG_KEY').text = key
        ET.SubElement(node, 'DATE_LIMIT').text = to_domino_date(exp_date)
        ET.SubElement(node, 'CFG_TYPE').text = metric.uid
        ET.SubElement(node, 'OPTIONS').text = product.uid
        if client_name is not None:
            ET.SubElement(node, 'LICENSEE_NAME').text = client_name
        return node
    @staticmethod
    def has_license(node, metric, key, product):
        try:
            return node.find('OPTIONS').text.find(product.uid) >= 0 and node.find('CFG_TYPE').text == metric.uid and node.find('CFG_KEY').text == key
        except:
            return False

    @staticmethod
    def remove_product(node, product):
        try:
            options = node.find('OPTIONS')
            products = options.text.split(",")
            products.remove(product.uid)
            options.text = ",".join(products)
            return True
        except:
            return False

    @staticmethod
    def has_no_products(node):
        try:
            return len(node.find('OPTIONS').text.strip()) == 0
        except:
            return True
    @staticmethod
    def exp_date(node): return from_domino_date(node.find('DATE_LIMIT').text)
    @staticmethod
    def expired(node): return CfgNode.exp_date(node) < datetime.date.today()
    @staticmethod
    def trial(node): return node.find('TRIAL') is not None
    @staticmethod
    def normal(node):
        return not CfgNode.trial(node) and not CfgNode.expired(node)
    @staticmethod
    def client_name(node):
        client_prop = node.find('LICENSEE_NAME')
        if client_prop is None:
            return None
        else:
            return client_prop.text

class Trial:
    def __init__(self, node = None):
        if node is None:
            self.node = ET.fromstring('<CFG>\n</CFG>')
        else:
            self.node = node
    @property
    def metric(self): return Metric.find_by_uid(self.node.find('CFG_TYPE').text, NONE)
    @property
    def key(self): return self.node.find('CFG_KEY').text
    @property
    def product(self): return Product.find(self.node.find('OPTIONS').text, UNKNOWN)
    @property
    def exp_date(self): return from_domino_date(self.node.find('DATE_LIMIT').text)
    @property
    def exp_date_string(self, node): return str(self.exp_date)
    @property
    def expired(self): return self.exp_date < datetime.date.today()
    @property
    def id(self):
        return Trial.make_id(self.metric, self.key, self.product)
    @staticmethod
    def make_id(metric, key, product):
        return '{0}.{1}.{2}'.format(product.id, metric, key)
    @staticmethod
    def make_file_name(metric, key, product):
        ''' M-INVENT.MOBILE.xxxxxx
            REYAL-POS.COMPUTER.xxxxxx
        '''
        return '{0}.{1}.{2}'.format(product.id, metric, key)

    def file_name(self):
        return Trial.make_file_name(self.metric, self.key, self.product)
    @staticmethod
    def load(file):
        trial = None
        if os.path.isfile(file):
            try:
                with open(file) as f:
                    trial = Trial(ET.fromstring(f.read()))
                if trial is not None:
                    if trial.id != os.path.basename(file):
                        log.error("invalid trial file %s ",file)
                        log.info("remove trial file %s", file)
                        os.remove(file)
                        trial = None
                else:
                    log.error("invalid trial file %s ",file)
            except:
                log.exception("invalid trial file %s ",file)
        return trial
    @staticmethod
    def file(account_id, metric, key, product):
        file_name = Trial.make_file_name(metric, key, product)
        return os.path.join(TRIAL_STORAGE(account_id), file_name)
    @staticmethod
    def get(account_id, metric, key, product):
        return Trial.load(Trial.file(account_id, metric, key, product))
    @staticmethod
    def find_all(account_id):
        ''' Формирование списка всех триалов за исключением 
            тех у кого истек срок действия
        '''
        trials = []
        for file in glob(TRIAL_STORAGE(account_id) + "/*"):
            trial = Trial.load(file)
            if trial is not None and not trial.expired:
                trials.append(trial)
        return trials
    @staticmethod
    def create(account_id, metric, key, product, client_name = None):
        ''' Создает триал или возвращает уже созданный триал
            Дважды создать один и тотже триал нельзя. Один раз созданный
            он живет вечно
        '''
        file = Trial.file(account_id, metric, key, product)
        # если есть возвращаем уже существующий
        trial = Trial.load(file)
        if trial is not None:
            return trial
        # нет - создаем 
        trial = Trial()
        trial.node = CfgNode.create(metric, key, product, TRIAL_DATE(), trial=True, client_name = client_name )
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            f.write(ET.tostring(trial.node, encoding='unicode'))
        return trial
## Evaluate maximum block size
#blocksize = (public_key.size() + 1) // 8

# Decode binary file certificate to the xml
def load_from_file(file):
    log.debug('%s', file)
    public_key = RSA.importKey(public_key_value)
    blocksize = (public_key.size() + 1) // 8
    data = b''
    if not os.path.isfile(file):
        return None
    log.debug('%s', file)
    with open(file, 'rb') as infile :
        while True :
            indata = infile.read(blocksize)
            if not indata: break
            outdata = public_key.encrypt(indata, 0)
            parts = outdata[0].split(b'\x00')
            data += parts[1]
    text = data.decode('cp1251')
    xml_file = file + '.xml'
    #log.debug('write %s', xml_file)
    with open(xml_file, 'w') as xml:
        xml.write(text)
    return  ET.fromstring(text)

# Encode xml & write it to binary file 
def save_to_file(xml, file):
    log.debug(file)
    if private_key_value is None:
        raise Exception('not private key')
    private_key = RSA.importKey(private_key_value)
    blocksize = (private_key.size() + 1) // 8
    bstring = ET.tostring(xml, encoding='cp1251')
    bstring = bstring[bstring.index(b'<DOMINO'):]
    xml_file = file + '.xml'
    with open(xml_file, "wb") as outfile:
        outfile.write(bstring)
        outfile.close()
    with open(xml_file, "rb") as infile, open(file, 'wb') as outfile :
        while True :
            indata = infile.read(blocksize - 11)
            if not indata : 
                break
            indata = b'\x00\x01' + b'\xFF' * (125 - len(indata)) + b'\x00' + indata
            outdata = private_key.decrypt(indata)
            if (len(outdata) < 128) :
                outfile.write(b'\x00' * (128 - len(outdata)))
            outfile.write(outdata)

def original_file(account_id):
   return os.path.join(ACCOUNTS, account_id, 'sft', ORIGINAL_FILENAME(account_id))

def final_file(account_id):
   return os.path.join(ACCOUNTS, account_id, 'sft', FINAL_FILENAME(account_id))

def get_sft_file(account_id):
   update(account_id)
   return final_file(account_id)

def load(account_id):
   x = update(account_id)
   if x is None:
      x = load_final_sertificate(account_id)
   return x

def load_original_sertificate(account_id):
   file = original_file(account_id)
   return load_from_file(file)

def load_final_sertificate(account_id):
   file = final_file(account_id)
   return load_from_file(file)

def save_final_sertificate(account_id, x):
   file = final_file(account_id)
   save_to_file(x, file)
   update_licenses_table(account_id, x)

def update(account_id):
    ''' Создает новый (final) сертификат на основании сгенеренного базовой системой
        сертификата. 
        Старый сертифика имее имя '<account_id>.sft', новый '<account_id>.final.sft'
        Суть преобразования это добавить в результирующий сертифика trials.
        Триалы добавляются при двух условиях:
            1. Соответствующей лицензии в базовом сертификате нет. Время ее использования не
               имеет значения
            2. Сам по себе trial уже существует и есть соответствующая запись в переке 
               где хранятся сертифкаты
        Возвращает ElrmrntTree если преобразования проведено и создан новый сертификат. При
        этом, старый (базовый) сертификат удаляется и это является признаком, что глвлго
        базового сертификата уже (еще) не создали
    '''
    # загружаем базовый сертификат
    x = load_original_sertificate(account_id)
    if x is None: 
        # базового сертификата нет. Это означчает, что со времени последнего
        # вызова его никто не сформировал и не выложил. возвращаем None, за
        # исключением случая отсутствия licenses.db 

        # проверяем наличие файла лицензий license.db. Отсутствие означает, что 
        # его следует посторитть в любом случае 
        if not os.path.isfile(LICENSES_DB(account_id)):
            log.info(f'Создание licenses.db для "{account_id}"')
            x = load_final_sertificate(account_id)
            update_licenses_table(account_id, x)
            return x
        return None
    else:
        log.info(f'Новый базовый сертификат для "{account_id}"')
        # базовый сертификат есть - загружен - следует в него вставить триалы
        # и сфортировать новый финальный сертификат
        # формируем список существующих лицензий (потенциальные файлы trial)
        used_trials = set()
        for node in x.findall('CFG'):
            metric = Metric.find_by_uid(node.find('CFG_TYPE').text)
            key = node.find('CFG_KEY').text
            options = node.find('OPTIONS').text
            if options is not None:
                for product_uid in options.split(','):
                    product = Product.find_by_uid(product_uid)
                    if product is None: # какой то левый продукт 
                        log.error("Неизвестный продукт %s", product_uid)
                        continue
                    trial_id = Trial.make_id(metric, key, product)
                    used_trials.add(trial_id)
        # перебираем список всех триалов и если есть
        # те, которых нет в сертификате и не просроченные то добавляем в конец
        #log.debug("used trials %s", ",".join(used_trials))
        for trial in Trial.find_all(account_id):
            trial_id = trial.id
            #log.debug("checked trial %s", trial_id)
            if trial_id not in used_trials:
                log.info("include trial %s", trial_id)
                x.append(trial.node)
        # сохраняем как финальный сертификат
        save_final_sertificate(account_id, x)
        # удааляем базовый сертификат
        #log.debug('remove %s', original_file(account_id))
        os.remove(original_file(account_id))
        #log.debug('return final sertificate')
        return x
   
def move_license(account_id, src_metric, src_key, dst_metric, dst_key, product):
    ''' Модифицируем финальный сертификат на предмет перемещения лицензии на продукт
        с обного устройства на другое 
        обязательным условием является следующие:
        1. У источника данная лицензия присутсвует (не триальная и не истекшая)
           Она может быть групповой (устаревшая структура)
        2. У приемника наоборот отсутствиет (либо триальная либо истекшая)
           Приемник тоже может быть групповой
        --------------------
        Что делает:
        1. Убирает переносимую лицензию из источника (убирает из списка продуктов или убирает запись вообще 
           если список состоит из обного продукта)
        2. Убирает лицензию из приемника (если есть). Опять же либо чичтит список продуктов, либо
           удаляет всю запись если продукт один
        3. Создает новую лицензионную запись с параметрами переносимой (дата, лицензиат)
    '''
    log.info('%s src_key=%s, dst_key=%s', account_id, src_key, dst_key)
    # производим обновление сертификата, на основании базового
    x = update(account_id)
    if x is None:
        # если нет - загружаем финальный сертификат
        x = load_final_sertificate(account_id)

    src_node = None # лицензия источника (которую у него отнимут)
    dst_node = None  # лицензия получателя (должня быть триальной или не быть вообще)
    for node in x.findall('CFG'):
        if CfgNode.has_license(node, src_metric, src_key, product):
            src_node = node
        elif CfgNode.has_license(node, dst_metric, dst_key, product):
            dst_node = node

    # АНАЛИЗ И УДАЛЕНИЕ ЛИЦЕНЗИЙ НА <product>
    if dst_node is not None:
        if CfgNode.trial(dst_node) or CfgNode.expired(dst_node):
            CfgNode.remove_product(dst_node, product)
            if CfgNode.has_no_products(node):
                x.remove(dst_node)
        else:
            return f"{dst_metric.name} {dst_key} имеет рабочую лицензию на продукт {product.id}. Замена такой лицензии невозможена."

    if src_node is None :
        return f"{src_metric.name} {src_key} : нет лиценззии {product.id} для переноса"
    elif CfgNode.trial(src_node):
        return f"{src_metric.name} {src_key} имеет временную лицензию на продукт {product.id}. Перенос такой лицензии невозможен."
    elif CfgNode.expired(src_node):
        return f"{src_metric.name} {src_key} имеет истекшую лицензию на продукт {product.id}. Перенос такой лицензии невозможен."
    else:
        # сохраняем данные переносимой лицензии
        src_exp_date = CfgNode.exp_date(src_node)
        src_client_name = CfgNode.client_name(node)
        # удаляем лицензию
        CfgNode.remove_product(src_node, product)
        if CfgNode.has_no_products(src_node):
            x.remove(src_node)

    # СОЗДАНИЕ НОВЙ ЛИЦЕНЗИИ
    node = CfgNode.create(dst_metric, dst_key, product, src_exp_date, client_name = src_client_name)
    x.append(node)
    save_final_sertificate(account_id, x)
    return ''

def check_trial(account_id, metric, key, product):
    x = update(account_id)
    if x is None:
        x = load_final_sertificate(account_id)
    
    trial = Trial.get(account_id, metric, key, product)
    if trial is None:
        trial = Trial.create(account_id, metric, key, product)
        x.append(trial.node)
        save_final_sertificate(account_id, x)

    return trial.exp_date.__str__()


class OneLicense:
    def __init__(self):
        self.product = UNKNOWN
        self.exp_date = datetime.date.max
        self.metric = NONE
        self.count = 1
        self.key = ''
        self.mark_no = ''
        self.serial_no = ''
        self.client_name = ''
        self.trial = False

    def clone(self, product):
        l = OneLicense()
        l.product = product
        l.exp_date = self.exp_date
        l.metric = self.metric
        l.count = self.count
        l.key = self.key 
        l.mark_no = self.mark_no 
        l.serial_no = self.serial_no
        l.client_name = self.client_name
        l.trial = self.trial
        return l

    @property
    def metric_uid(self):
      return self.metric.uid
    @metric_uid.setter
    def metric_uid(self, value):
        metric = Metric.find(value, NONE)
        if metric.is_hasp:
            self.metric = NETHASP
        elif metric.is_memohasp:
            self.metric = MEMOHASP
        else:
            self.metric = metric

    @staticmethod
    def create_key_id(metric, key):
        return '{0}:{1}'.format(metric.id, key)
    @property
    def key_id(self):
      return OneLicense.create_key_id(self.metric, self.key)

    @property
    def expire(self):
        return self.exp_date < datetime.date.today()

    @property
    def normal(self):
        if self.trial or self.exp_date < datetime.date.today():
            return False
        else:
            return True

    @property
    def domino_exp_date(self):
        return to_domino_date(self.exp_date)
    @domino_exp_date.setter
    def domino_exp_date(self, value):
        self.exp_date = from_domino_date(value)

    def __str__(self):
        return "{0}:{1} {2} {3}".format(self.metric.id, self.key, self.product.id, self.count)

    @property
    def id(self):
        return "{0}:{1}". format(self.key_id, self.product.id) 

class AccountLicense:
    def __init__(self, account_id = None):
        self.account = account_id
        self.xml = load(account_id = account_id)
        if self.xml is None:
            raise Exception(f'Не определена лицензия для "{account_id}"')
        self._licenses = None
        for node in self.xml:
            if node.tag == 'DOMINO_CERTIFICATE_HEADER':
                for p in node:
                    if p.tag == 'NAME':
                        self.account_id = p.text
                    elif p == 'DATE':
                        self.date = from_domino_date(p.text)
                    elif p.tag == 'CLIENT_NAME':
                        self.client_name = p.text

    def get_all_licenses(self):
        if self._licenses is None:
            self._licenses = []
            for node in self.xml:
                if node.tag == 'HASP':
                    l = OneLicense()
                    l.product = DOMINO
                    hasp_type = None
                    for p in node:
                        if p.tag == 'HASP_PARTY':
                            pass
                        elif p.tag == 'HASP_TYPE':
                            hasp_type = p.text
                            l.metric_uid = p.text
                        elif p.tag == 'HASP_ID':
                            l.key = p.text
                        elif p.tag == 'SERIAL_NO':
                            l.serial_no = p.text
                        elif p.tag == 'MARK_NO':
                            l.mark_no = p.text
                        elif p.tag == 'LICENSE_COUNT':
                            l.count = int(p.text)
                        elif p.tag == 'LICENSEE_NAME':
                            l.client_name = p.text
                    self._licenses.append(l)
                elif node.tag == 'CFG':
                    l = OneLicense()
                    options = None
                    for p in node:
                        if p.tag == 'TRIAL':
                            l.trial = True
                        if p.tag == 'CFG_TYPE':
                            l.metric_uid = p.text
                        elif p.tag == 'CFG_KEY':
                            l.key = p.text
                        elif p.tag == 'DATE_LIMIT':
                            l.domino_exp_date = p.text
                        elif p.tag == 'LICENSEE_NAME':
                            l.client_name = p.text
                        elif p.tag == 'OPTIONS':
                            options = p.text
                    if l.client_name is None:
                        l.client_name  = self.client_name
                    if options is not None:
                        for product_uid in options.split(','):
                            product = Product.find(product_uid, UNKNOWN)
                            clone = l.clone(product)
                            #log.debug("%s", lp.id)
                            self._licenses.append(clone)
                    else:
                        log.debug("%s no options", l.id)
                elif node.tag == 'METRICS':
                    for metric in node:
                        l = OneLicense()
                        for p in metric:
                            if p.tag == 'TYPE':
                                l.metric_uid = p.text
                            elif p.tag == 'VALUE':
                                l.key = p.text
                            elif p.tag == 'DATE_LIMIT':
                                l.domino_exp_date = p.text
                        if l.metric == FSRAR:
                            l.product = RETAIL_ALCO
                        elif l.metric == INN:
                            l.product = RETAIL_STORE_KZ
                        else:
                            l.product = UNKNOWN
                        self._licenses.append(l)
        return self._licenses

    def get_license(self, metric, key, product):
        for license in self.get_all_licenses():
            if license.metric.id == metric.id and license.key == key and license.product.id == product.id:
                return license
        return None

    def get_metric_licenses(self, metric, key = None):
        #log.debug(metric.id)
        licenses = []
        for license in self.get_all_licenses():
            if (license.metric.id in metric.id) and (key is None or license.key == key):
                #log.debug(license.id)
                licenses.append(license) 
        return licenses

    def get_product_licenses(self, product):
        licenses = []
        for license in self.get_all_licenses():
            if license.product == product:
                licenses.append(license) 
        return licenses

    @staticmethod
    def key_id(metric, key):
        return '{0}:{1}'.format(metric.id, key)

class AccountLicenseDB:
    def __init__(self, account_id):
        update(account_id)
        create_licenses_table(account_id)
        self.conn = sqlite3.connect(LICENSES_DB(account_id))
        self.cur = self.conn.cursor()
        
    def select(self, query, params):
        self.cur.execute(query, params)
        r = self.cur.fetchall()
        return r

    def count(self, where, params):
        self.cur.execute(f'select count(*) from licenses where {where} ', params)
        return self.cur.fetchone()[0]

    @staticmethod
    def get_products_for_purchase(account_id, metric_id, key):
        purchase = []
        with sqlite3.connect(LICENSES_DB(account_id)) as conn:
            cur = conn.cursor()
            cur.execute('select product_id, trial, exp_date from licenses where account_id=? and metric_id=? and key=?;',
            [account_id, metric_id, key])
            today = datetime.date.today().isoformat()
            for product_id, trial, exp_date in cur:
                expire = exp_date is not None and exp_date < today 
                if trial == '0' or expire:
                    purchase.append(product_id)
        return purchase

class one_license_record:
    def __init__(self, account_id):
        self.account_id = account_id
        self.metric_id = NONE.id
        self.product_id = UNKNOWN.id
        self.key = None
        self.qty = 1
        self.exp_date = None
        self.trial = False
        self.info = {}

    def insert_into(self, cur):
        info = json.dumps(self.info, ensure_ascii=False)
        #log.debug(f'{os.getpid()} : {self.account_id}, {self.metric_id}, {self.key}, {self.product_id} {info}')
        cur.execute(
        '''
            insert or replace into licenses 
            (account_id, metric_id, key, product_id, qty, exp_date, trial, info) 
            values (?, ?, ?, ?, ?, ?, ?, ?); 
        ''' , 
        [self.account_id, self.metric_id, self.key, self.product_id, 
        self.qty, self.exp_date, int(self.trial), info]
        )   

def create_licenses_table(account_id):
    xml = load_final_sertificate(account_id)
    update_licenses_table(account_id, xml)

def update_licenses_table(account_id, xml):
    #log.info(f'Обновление/создание таблицы "licenses" для "{account_id}"')
    licenses_db = LICENSES_DB(account_id)
    os.makedirs(os.path.dirname(licenses_db), exist_ok=True)
    conn = sqlite3.connect(licenses_db)
    with conn:
        conn.execute('''
        create table if not exists licenses (
            account_id  text not null,
            metric_id   text not null, 
            key         text not null, 
            product_id  text not null, 
            qty         int not null,
            exp_date,
            trial       int not null default(0),
            info        blob,
            primary key (account_id, metric_id, key, product_id)
            );
        ''')
        cur = conn.cursor()
        cur.execute('delete from licenses where account_id=?;', [account_id]) 
        if xml is None:
            return
        for node in xml:
            if node.tag == 'DOMINO_CERTIFICATE_HEADER':
                for p in node:
                    if p.tag == 'CLIENT_NAME':
                        client_name = p.text

            elif node.tag == 'HASP':
                r = one_license_record(account_id)
                r.product_id = DOMINO.id
                for p in node:
                    if p.tag == 'HASP_TYPE':
                        r.info['HASP_TYPE'] = p.text
                        metric = Metric.find(p.text, NONE)
                        if metric.is_hasp:
                            r.metric_id = NETHASP.id
                        elif metric.is_memohasp:
                            r.metric_id = MEMOHASP.id
                        else:
                            r.metric_id = metric.id
                    elif p.tag == 'HASP_ID':
                        r.key = p.text
                    elif p.tag == 'LICENSE_COUNT':
                        r.qty = int(p.text)
                    else:
                        r.info[p.tag] = p.text
                #print(f'\n{json.dumps(r.info,ensure_ascii=False)}')
                r.insert_into(cur)

            elif node.tag == 'CFG':
                r = one_license_record(account_id)
                options = None
                for p in node:
                    if p.tag == 'TRIAL':
                        r.trial = True
                    if p.tag == 'CFG_TYPE':
                        metric = Metric.find(p.text, NONE)
                        r.metric_id = metric.id
                    elif p.tag == 'CFG_KEY':
                        r.key = p.text
                    elif p.tag == 'DATE_LIMIT':
                        r.exp_date = from_domino_date(p.text)
                    elif p.tag == 'OPTIONS':
                        options = p.text
                    else:
                        r.info[p.tag] = p.text
                        
                if r.info.get('LICENSEE_NAME') is None:
                    r.info['LICENSEE_NAME'] = client_name

                if options is not None:
                    for product_uid in options.split(','):
                        product = Product.find(product_uid, UNKNOWN)
                        r.product_id = product.id
                        r.insert_into(cur)

            elif node.tag == 'METRICS':
                for metric_item in node:
                    r = one_license_record(account_id)
                    metric = NONE
                    for p in metric_item:
                        if p.tag == 'TYPE':
                            metric = Metric.find(p.text, NONE)
                            r.metric_id = metric.id
                        elif p.tag == 'VALUE':
                            r.key = p.text
                        elif p.tag == 'DATE_LIMIT':
                            r.exp_date = from_domino_date(p.text)
                        else:
                            r.info[p.tag] = p.text
                    if metric == FSRAR:
                        r.product_id = RETAIL_ALCO.id
                    elif metric == INN:
                        r.product_id = RETAIL_STORE_KZ.id
                    r.insert_into(cur)


