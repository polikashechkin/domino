import os, sys
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path :
    sys.path.append(path)

from domino.core import log, DOMINO_ROOT, Version
from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning

console = Console()

def install(module_id, version):
    folder = os.path.join(DOMINO_ROOT, 'products', module_id, str(version))
    os.makedirs(folder, exist_ok=True)
    module_zip = os.path.join(DOMINO_ROOT, 'products', module_id, f'{module_id}.zip')
    console.system(f'curl https://rs.domino.ru/public/products/{module_id}/{version.draft()}/{version}/{module_id}.zip > {module_zip}')
    console.system(f'unzip -qu {module_zip} -d {folder}')
    os.remove(module_zip)
    #------------------------------
    requirements_txt = os.path.join(folder, 'python', 'requirements.txt')
    if os.path.isfile(requirements_txt):
        console.system(f'pip3 -q install -r {requirements_txt}')
    on_install_py = os.path.join(folder, 'python','on_install.py')
    if os.path.isfile(on_install_py):
        console.run(on_install_py)

def help():
    print('domino install <module> <version> : Зарузить и установить версию модуля') 

if __name__ == "__main__":
    module_id = console.arg(1)
    version = Version.parse(console.arg(2))
    if module_id is None:
        help()
        sys.exit(1)
    install(module_id, version)
    

