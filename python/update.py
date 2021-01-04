
import os,sys,shutil
from domino.core import log, Server, start_log
from domino.cli import Console
from domino.jobs import Job
from domino.globalstore import GlobalStore

def symlink(job, src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)
    job.log('create symlink "{0}" to "{1}"'.format(dst, src))

def execute_py(job, file_py, version):
    if os.path.isfile(file_py):
        job.log(f'python3.6 {file_py} {version}')
        os.system(f'python3.6 {file_py} {version}')

def create_uwsgi_socket(job, product, version, sock_name = None):
    job.log(f'Создание/обновление socket "{sock_name}" для {product}.{version}')
    #print(f'create uwsgi socket {product} {version} {sock_name}')
    os.makedirs('/DOMINO/uwsgi/sockets', exist_ok=True)
    os.makedirs('/DOMINO/uwsgi/vassals', exist_ok=True)
    if sock_name is None:
        sock_name = str(version)
    sock = f'/DOMINO/uwsgi/sockets/{str(product)}.{sock_name}.sock'
    vassal = f'/DOMINO/uwsgi/vassals/{str(product)}.{sock_name}.ini'
    with open(vassal, 'w') as f:
        f.write(f'[uwsgi]\n')
        f.write(f'chdir = /DOMINO/products/{product}/{version}/python\n')
        f.write(f'socket = {sock}\n')
        f.write(f'touch-reload = /DOMINO/products/{product}/{version}/python/application.py\n')
        f.write(f'python-autoreload=1\n')

def install_cli(job, cli_file_py, cli_name):
    if os.path.isfile(cli_file_py):
        job.log(f'Установка cli "{cli_name}" как "{cli_file_py}"')
        bat_file = os.path.join('/usr/local/bin', cli_name)
        with open(bat_file, 'w') as f:
            f.write(f'python3.6 {cli_file_py} $*')
        os.system(f'chmod 777 {bat_file}')
   
def on_install(job, product, version):
    '''
    Выполняет действия после установки продукта
    Устанвливает дополнительные пакеты python
    и индивидуальные действия из файла .../python/on_install.py
    '''
    version_folder = Server.version_folder(product, version)
    requirements_txt = os.path.join(version_folder, 'python', 'requirements.txt')
    if os.path.isfile(requirements_txt):
        job.log('Установка/проверка дополнительных пакетов python')
        os.system(f'pip3.6 -q install -r {requirements_txt}')
    on_install_py = os.path.join(version_folder, 'python','on_install.py')
    execute_py(job, on_install_py, version)


def activate(job, product, version):
    '''
    Определяет версию продукта, как активную. Версия должна быть предварительно
    установлена, соответственно вызов для данной версии будет
    сервер//pruduct/active/...
    Вызов по номеру версии (//product/xx.xx.xx.xx/python/...) не создается. 
    Он создается при установке  продукта (install) и удаляется при удалении продукта (remove)
    Если в директории python есть файл вида <продукт>.usr.py он устанавливается как 
    консольный вызов данного пролукта
    
    '''
    job.log(f'activate {product} {version}')
    if not Server.version_exists(product, version):
        job.log(f'Версия "{product}.{version}" не установлена')
        return 
    version_folder = Server.version_folder(product, version)
    python_folder = os.path.join(version_folder, 'python')
    product_folder = Server.product_folder(product)
    symlink(job, version_folder, os.path.join(product_folder, 'active'))
    create_uwsgi_socket(job, product, version, 'active')
    # Заносим данные в конфигурацию сервера
    config = Server.get_config()
    config.set_version(product, version)
    config.save()
    # Установка Command Line Interfaces (CLI)
    install_cli(job, os.path.join(python_folder, f'{product}.usr.py'), product)
    install_cli(job, os.path.join(python_folder, f'{product}.cli.py'), product)
    on_activate_py = os.path.join(python_folder, 'on_activate.py')
    execute_py(job, on_activate_py, version)

def install(job, product, version = None):
    '''
    Устанавливает версияю продукта из репозитория и делает ее вызываемой
    Если версия не задана, то берется последняя версия
    Если версия уже установлена, то ночего не делается
    '''
    gs = GlobalStore()
    if version is None:
        version = gs.get_latest_version(product)
    elif version.is_draft:
        version = gs.get_latest_version_of_draft(product, version)
    version_folder = Server.version_folder(product, version)
    if os.path.isdir(version_folder):
        pass
        #job.log(f'Версия {product} {version} уже установлена')
    else:
        job.log(f'Установка {product}.{version}')
        distro_file = os.path.join(job.temp, 'distro.zip')
        gs.download_distro(product, version, distro_file)
        shutil.unpack_archive(distro_file, extract_dir=Server.version_folder(product, version))
        #job.log(f'Версия {product} {version} установлена')

    # Не активируем установленные версии пока
    #if product != 'domino':
    #    create_uwsgi_socket(job, product, version)
    #    on_install(job, product, version)

    return version

JOB_NAME = 'domino.update'
if __name__ == "__main__":
    try:
        console = Console()
        job_id = console.arg(1)
        with Job.open(job_id) as job:
            job.start_if_not_exists(JOB_NAME)
            config = Server.get_config()
            #job.log('Проверска всех установленных модулей')
            for product in config.get_products():
                try:
                    active_version = config.get_version(product)
                    version = install(job, product, active_version.draft())
                    if active_version.is_draft:
                        job.log(f'Версия {product}.{version} не будет активирована, поскольку ативна версия в разработке {active_version}')
                    elif version == active_version:
                        #job.log(f'Версия {product}.{version} уже активирована')
                        pass
                    else:
                        activate(job, product, version)
                except BaseException as ex:
                    log.exception(JOB_NAME)
                    job.log(f'{ex}')
    except:
        start_log.exception(JOB_NAME)
