import os, sys
import json
import shutil
import requests
from domino.log import log
import datetime
import subprocess
import pickle

SERVER_CONFIG_FILE = '/DOMINO/domino.config.info.json'
INSTALLED_PRODUCTS = '/DOMINO/products'
STORE_PRODUCTS = '/DOMINO/public/products'
PUBLIC_PRODUCTS = '/DOMINO/public/products'

JOBS = '/DOMINO/jobs'
JOB_REPORTS = '/DOMINO/jobs.reports'

class Version:
    def __init__(self, major, minor, draft, build = 10000):
        self.NONE_RELEASE = 10000
        self.n = [int(major), int(minor), int(draft), int(build)]
        self._make_id()

    def _make_id(self):
        if self.n[3] == 10000:
            self.id = '{0}.{1}.{2}'.format(self.n[0], self.n[1], self.n[2])
        else:
            self.id = '{0}.{1}.{2}.{3}'.format(self.n[0], self.n[1], self.n[2], self.n[3])
        
    @property
    def is_draft(self):
        return self.n[3] == self.NONE_RELEASE
    def is_draft_of(self, other):
        return (self.compare(other, 3) == 0) and (self.n[3] == self.NONE_RELEASE)
    def draft(self):
        return Version(self.n[0], self.n[1], self.n[2])

    def next(self):
        if self.n[3] == self.NONE_RELEASE:
            return Version(self.n[0], self.n[1], self.n[2], 0)
        else:
            return Version(self.n[0], self.n[1], self.n[2], self.n[3] + 1)
    @staticmethod
    def parse(s):
        try:
            parts = s.split('.')
            l = len(parts)
            if l == 3:
                return Version(parts[0], parts[1], parts[2])
            elif l == 4:
                return Version(parts[0], parts[1], parts[2], parts[3])
            else:
                return None
        except:
            return None

    @staticmethod
    def versions_dump(versions):
        versions_id = []
        for version in versions:
            versions_id.append(version.id)
        return json.dumps(versions_id)

    def compare(self, other, len = 4):
        for i in range(len):
            if self.n[i] < other.n[i]:
                return -1
            elif self.n[i] > other.n[i]:
                return 1
        return 0
        
    def __eq__(self, other): # x == y вызывает x.__eq__(y).
        return self.compare(other) == 0
    def __ne__(self, other): # x != y вызывает x.__ne__(y)
        return self.compare(other) != 0
    def __lt__(self, other): # x < y вызывает x.__lt__(y).
        return self.compare(other) < 0 
    def __le__(self, other): # x ≤ y вызывает x.__le__(y).
        return self.compare(other) <= 0 
    def __gt__(self, other): #  x > y вызывает x.__gt__(y).
        return self.compare(other) > 0
    def __ge__(self, other): # x ≥ y вызывает x.__ge__(y)
        return self.compare(other) >= 0 
    def __hash__(self):
        return self.id.__hash__()

    def __str__(self):
        return self.id

class JobReport:
    def __init__(self, product, name):
        self.product = product
        self.name = name
        self.id=f'{product}/{name}'
        self.folder = os.path.join(JOB_REPORTS, product, name)
        self.update()

    @property
    def working(self):
        return self.status == Job.Working

    @property
    def status(self):
        status = self.info.get('status')
        return status if status is not None else Job.Success

    @property
    def start(self):
        return self.info.get('start').strftime('%Y-%m-%d %H:%M:%S') 

    @property
    def end(self):
        end = self.info.get('end')
        if end is None:
            return ''
        else:
            return end.strftime('%Y-%m-%d %H:%M:%S') 
    @property
    def message(self):
        return self.info.get('message')

    @property
    def time(self):
        start = self.info.get('start')
        end = self.info.get('end')
        if end is None:
            end = datetime.datetime.now()
        return str(end - start)

    def exists(self):
        return os.path.exists(self.folder)

    def update(self):
        if self.exists():
            info_file = os.path.join(self.folder, "info")
            with open(info_file, "rb") as f:
                self.info = pickle.load(f)
        else:
            self.info = {}

    @staticmethod
    def findall(product):
        ''' Список всех задач
        '''
        jobs = []
        folder = os.path.join(JOB_REPORTS, product)
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                job = JobReport(product, name)
                jobs.append(job)
        return jobs

class Job:
    Error = 'error'
    Success = 'success'
    Working = 'working'

    @staticmethod
    def run(request, program, args):
        lib = os.path.join('/DOMINO' + request.path.split('/web')[0], 'python')
        params = []
        params.append('python3.6')
        params.append(os.path.join(lib, program))
        for arg in args:
            params.append(str(arg))
        return subprocess.Popen(params)
    
    @staticmethod
    def working(product, job_name):
        return os.path.exists(os.path.join(JOBS, product, job_name))

    def __init__(self, product, name):
        self.product = product
        self.name = name
        self.info = {'start' : datetime.datetime.now()}
        self.info['status'] = Job.Working
        self.info['message'] = ''
        self.info['pid'] = os.getpid()

        self.folder = os.path.join(JOBS, product, name)

        try:
            os.makedirs(self.folder)
        except:
            raise Exception(f"Задача {product}/{name} уже выполняется")
            
        self.report_folder = os.path.join(JOB_REPORTS, product, name)
        os.makedirs(self.report_folder, exist_ok=True)
        self._save_info()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is None:
            self.close()
        else:
            self.info['exception_type'] = exception_type
            self.info['exception_value'] = exception_value
            #self.info['traceback'] = traceback
            self.close(Job.Error, str(exception_value))

    def close(self, status = None, message = None):
        shutil.rmtree(self.folder)
        if status is not None:
            self.info['status'] = status
        else:
            if self.info['status'] == Job.Working:
                self.info['status'] = Job.Success
        if message is not None:
            self.info['message'] = str(message)
        self.info['end'] = datetime.datetime.now()
        self._save_info()

    def _save_info(self):
        os.makedirs(self.report_folder, exist_ok = True)
        info_file = os.path.join(self.report_folder, "info")
        with open(info_file, "wb") as f:
            pickle.dump(self.info, f)
        
    def success(self, message):
        self.info['message'] = message
        self.info['status'] = Job.Success
        self._save_info()

    def error(self, message):
        self.info['message'] = str(message)
        self.info['status'] = Job.Error
        self._save_info()

class ProductInfo:

    osComputer = 'server'
    osServer = 'computer'
    osUser = 'user'
    osMobile = 'mobile'
    osProject = 'project'

    def __init__(self, js = {}):
        self.js = js

    @property
    def id(self):
        return self.js.get('id')

    def __str__(self):
        return self.id

    def dumps(self):
        return json.dumps(self.js)

    def dump(self, f):
        json.dump(self.js, f)

    @staticmethod
    def loads(s):
        return ProductInfo(json.loads(s))

    @staticmethod
    def load(f):
        return ProductInfo(json.load(f))

class VersionInfo:
    def __init__(self, js = {}):
        #log.debug(json.dumps(js))
        self.js = js

    @staticmethod
    def loads(s):
        return VersionInfo(json.loads(s))

    @staticmethod
    def load(f):
        return VersionInfo(json.load(f))

    def dumps(self):
        return json.dumps(self.js)

    def dump(self, f):
        return json.dump(self.js, f)
    
    def write(self, folder):
        file = os.path.join(folder, 'info.json')
        with open(file, 'w') as f:
            json.dump(self.js, f, ensure_ascii=False)

    @staticmethod
    def read(self, folder):
        file = os.path.join(folder, 'info.json')
        with open(file, 'r') as f:
            return VersionInfo(json.load(f))

    @property
    def version(self):
        return Version.parse(self.js.get('version'))
    @version.setter
    def version(self, value):
        self.js['version'] = str(value)

    @property
    def product(self):
        return self.js.get('product')
    @product.setter
    def product(self, value):
        self.js['product'] = str(value)

    @property
    def id(self):
        return self.js.get('version')

    @property
    def description(self):
        return self.js.get('description', '')

    @property
    def creation_time(self):
        return self.js.get('creation_date', '')

    @property
    def creation_date(self):
        return self.js.get('creation_date', '')

    def __str__(self):
        return '{0} от {1}'.format(self.version, self.creation_time)

class Config:
    def __init__(self, id):
        self.id = str(id)
        self.js = {'id' : id, 'products' : {} }

    @property
    def products(self):
        return self.js['products']

    def _next_pos(self):
        max = 0
        for pos in self.js['products'].keys():
            i = int(pos)
            if max < i:
                max = i
        return str(max + 1)

    def get_product(self, product_id, create=False):
        for product in self.js['products'].values():
            if product['id'] == str(product_id):
                return product
        if create:
            product = {'product' : product_id}
            self.js['products'][self._next_pos()] = product
            return product
        else:
            return None
        
    def get_version(self, product_id):
        product = self.get_product(product_id)
        if product is not None:
            return Version.parse(product.get('version'))
        else:
            return None

    def set_version(self, product_id, version):
        product = self.get_product(product_id, create=True)
        if product is not None:
            product['version'] = str(version)
        else:
            return None

    def save(self):
        os.makedirs('/DOMINO/configs', exist_ok=True)
        file = os.path.join('/DOMINO/configs', self.id + ".json")
        with open(file, 'w') as f:
            json.dump(self.js, f)

    @staticmethod
    def get(id):
        config = None
        file = os.path.join('/DOMINO/configs', id + ".json")
        if os.path.isfile(file):
            with open(file, 'r') as f:
                js = json.load(f)
            config = Config(id)
            config.js = js
        return config

    def __str__(self):
        return self.id


class ServerConfig:
    ''' 
    Конфигурация сервера
    Хранится в файле /DOMINO/domino.config.info.ison : 
        {
            server_version : <версия сервера>
            password : <пароль доступа к серверу>
            products : [
                {"name":<идентификатор продукта>, "version":<рабочая версия>, "history":<список предыдущих версий>}
            ]
        }
    Для каждого продукта существует одна запись. В стуктуре этого не отражено по историческим причинам
    '''
    def __init__(self):
        with open(SERVER_CONFIG_FILE) as f:
            self.js = json.load(f)
            self.products = self.js.get('products')
            if self.products is None:
                self.products = []
                self.js['products'] = self.products

    def save(self):
        with open(SERVER_CONFIG_FILE, 'w') as f:
            json.dump(self.js, f)
        
    def get_products(self):
        products = []
        for product in self.products:
            products.append(product['name'])
        return products

    def get_product(self, product, create=False):
        for j_product in self.products:
            if j_product['name'] == str(product):
                return j_product
        if create:
            j_product = {'name':str(product)}
            self.products.append(j_product)
            return j_product
        else:
            return None

    def get_version(self, product):
        j_product = self.get_product(product)
        if j_product is not None:
            return Version.parse(j_product.get('version'))
        else:
            return None

    def get_history_version(self, product):
        j_product = self.get_product(str(product))
        if j_product is not None:
            return Version.parse(j_product.get('history'))
        else:
            return None

    def set_version(self, product, version):
        j_product = self.get_product(product, create=True)
        j_product['history'] = j_product.get('version')
        j_product['version'] = str(version)
        self.save()
        log.info("%s %s активирована", str(product), str(version))

class Distro:
    def __init__(self, product, version):
        self.product = product
        self.version = Version.parse(str(version))
        self.file_name = "{0}.{1}.zip".format(product, version)
        self.folder = os.path.join(STORE_PRODUCTS, str(product), str(version))
        self.file = os.path.join(self.folder, self.file_name)

    @staticmethod
    def product_folder(product):
        return os.path.join(STORE_PRODUCTS, str(product))

    @property
    def exists(self):
        return os.path.isfile(self.file)

    def version_info(self):
        info_file = os.path.join(self.folder, "info.json")
        if os.path.isfile(info_file):
            with open(info_file, "r") as f:
                return VersionInfo.load(f)
        return None

    @staticmethod
    def get_versions(product, draft = None):
        versions = []
        product_folder = Distro.product_folder(product)
        if os.path.isdir(product_folder):
            for version_id in os.listdir(product_folder):
                version = Version.parse(version_id)
                if version is not None:
                    if draft is None or draft.is_draft_of(version):
                        versions.append(version)
        return versions

    @staticmethod
    def get_latest_version(product, draft = None):
        return max(Distro.get_versions(product, draft), default=None)

class Server:
    @staticmethod
    def product_folder(product):
        return os.path.join(INSTALLED_PRODUCTS, str(product))

    @staticmethod
    def version_folder(product, version):
        return os.path.join(INSTALLED_PRODUCTS, str(product), str(version))

    @staticmethod
    def get_products():
        products = []
        for product_id in os.listdir(INSTALLED_PRODUCTS):
            if os.path.isdir(os.path.join(INSTALLED_PRODUCTS, product_id)):
                products.append(product_id)
        return products

    @staticmethod
    def version_exists(product, version):
        return os.path.exists(Server.version_folder(product, version))

    @staticmethod
    def get_versions(product):
        versions = []
        dir = Server.product_folder(product)
        if os.path.isdir(dir):
            for version_id in os.listdir(dir):
                version = Version.parse(version_id)
                if version is not None:
                    versions.append(version)
        return versions

    @staticmethod
    def get_drafts(product):
        drafts = []
        for version in Server.get_versions(product):
            if version.is_draft:
                drafts.append(version)
        return drafts

    @staticmethod
    def get_versions_of_draft(product, draft):
        versions = []
        if draft is not None and draft.is_draft:
            for version in Server.get_versions(product):
                if version.is_draft: continue
                if not draft.is_draft_of(version): continue
                versions.append(version)
        return versions

    @staticmethod
    def get_latest_version_of_draft(product, draft):
        return max(Server.get_versions_of_draft(product, draft), default = None)

    @staticmethod
    def get_latest_version(product):
        return max(Server.get_versions(product), default = None)

    @staticmethod
    def get_version_info(product, version):
        info_file = os.path.join(Server.version_folder(product, version), 'info.json')
        if os.path.isfile(info_file):
            with open(info_file, "r") as f:
                return VersionInfo(json.load(f))
        return None

    @staticmethod
    def reload_server():
        resp = requests.get('http://localhost/domino/nginx/refresh.lua?sk=dev',  verify=False)
        if resp.status_code != 200:
            raise BaseException('Ошибка перезагрузки сервера')
        log.info("Сервер перезагружен")

    @staticmethod
    def install(product, version, distro_file):
        if not Server.version_exists(product, version):
            version_folder = Server.version_folder(product, version)
            os.makedirs(version_folder, exist_ok=True)
            shutil.unpack_archive(distro_file, extract_dir=version_folder)
    @staticmethod
    def get_config():
        return ServerConfig()


class Instance:
    @staticmethod
    def config():
        return ServerConfig()
    
    @staticmethod
    def get_server_config():
        return ServerConfig()

    @staticmethod
    def version_exists(product, version):
        return os.path.exists(os.path.join(INSTALLED_PRODUCTS, str(product), str(version)))

    @staticmethod
    def get_products():
        products = []
        for product_id in os.listdir(INSTALLED_PRODUCTS):
            if os.path.isdir(os.path.join(INSTALLED_PRODUCTS, product_id)):
                products.append(product_id)
        return products

    @staticmethod
    def get_versions(product):
        versions = []
        dir = os.path.join(INSTALLED_PRODUCTS, str(product))
        if os.path.isdir(dir):
            for version_id in os.listdir(dir):
                version = Version.parse(version_id)
                if version is not None:
                    versions.append(version)
        return versions

    @staticmethod
    def get_drafts(product):
        drafts = []
        for version in Instance.get_versions(product):
            if version.is_draft:
                drafts.append(version)
        return drafts

    @staticmethod
    def get_versions_of_draft(product, draft):
        versions = []
        if draft is not None and draft.is_draft:
            dir = os.path.join(INSTALLED_PRODUCTS, str(product))
            if os.path.isdir(dir):
                for version_id in os.listdir(dir):
                    version = Version.parse(version_id)
                    if version is None: continue
                    if version.is_draft: continue
                    if not draft.is_draft_of(version): continue
                    versions.append(version)
        return versions

    @staticmethod
    def get_latest_version_of_draft(product, draft):
        latest = None
        for version in Instance.get_versions_of_draft(product, draft):
            if latest is None or latest < version:
                latest = version
        return latest

    @staticmethod
    def get_version_info(product, version):
        info_file = os.path.join(Instance.version_folder(product, version), 'info.json')
        if os.path.isfile(info_file):
            with open(info_file, "r") as f:
                return VersionInfo(json.load(f))
        return None
    @staticmethod
    def product_folder(product):
        return os.path.join(INSTALLED_PRODUCTS, str(product))

    @staticmethod
    def version_folder(product, version):
        return os.path.join(INSTALLED_PRODUCTS, str(product), str(version))

    @staticmethod
    def reload_server():
        resp = requests.get('http://localhost/domino/nginx/refresh.lua?sk=dev',  verify=False)
        if resp.status_code != 200:
            raise BaseException('Ошибка перезагрузки сервера')
        log.info("Сервер перезагружен")

    @staticmethod
    def install(product_id, version_id):
        if Instance.is_version_installed(product_id, version_id):
            log.info('%s %s уже установлена', product_id, version_id)
            return
        distro_file = Instance.distro_file(product_id, version_id)
        version_path = Instance.installed_version_dir(product_id, version_id)
        os.makedirs(version_path, exist_ok=True)
        shutil.unpack_archive(distro_file, extract_dir=version_path)
        log.info('%s %s установлена', product_id, version_id)


def last_install_version(product, account) :
   pass


def last_active_version(product, account) :
   pass

  
