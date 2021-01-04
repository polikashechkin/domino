import sqlite3, json, sys
from domino.page import Page as BasePage
from domino.core import log
from subprocess import Popen, PIPE

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)

    def __call__(self):
        self.title('Домино (сервер приложений)')
        table = self.table('params')
        table.row('version').fields("Версия", f'{self.application.version}')
        r = table.row()
        r.text('python')
        r.text(f'{sys.version}')
        r = table.row()
        r.text('nginx')
        p = Popen('nginx -v', shell=True, stderr=PIPE, close_fds=True)
        r.text(p.stderr.read().decode('UTF-8'))

        r = table.row()
        r.text('uwsgi')
        p = Popen('uwsgi --version', shell=True, stdout=PIPE, close_fds=True)
        r.text(p.stdout.read().decode('UTF-8'))
    

