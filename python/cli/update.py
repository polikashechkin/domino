import os, sys
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

from domino.core import log, DOMINO_ROOT, Version, IS_WINDOWS, IS_LINUX
from domino.cli import print_comment, arg, print_error, print_header, Console, print_help,header, print_warning

from install import install
from on_activate import on_activate
from activate import activate

console = Console()

def help():
    print('domino update <module> <version>  : Обновление установленного модуля до заданной версии') 

if __name__ == "__main__":
    module_id = console.arg(1)
    version = Version.parse(console.arg(2))
    if module_id is None or version is None:
        help()
        sys.exit()
    install(module_id, version)
    on_activate(module_id, version, None)
    activate(module_id, version)
