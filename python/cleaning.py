import os, time, json, sys, datetime, sqlite3
from time import sleep
from domino.jobs import query_job2, start_job, JOBS_DB
#from domino.crontab import CronJob
from domino.jobs import Proc
from domino.core import log
from domino.page import Page
from domino.jobs_pages import TabControl

DESCRIPTION = 'Чистка системы'

tabs = TabControl('cleaning_tabs')
tabs.item('schedule', 'Расписание', 'print_schedule')
tabs.item('manually', 'Ручной запуск', 'print_manually')

class ThePage(Page):
    def __init__(self, application, request):
        super().__init__(application, request, controls=[tabs])
        #self.controls.append(tabs)
        self.job_id = self.attribute('job_id')
        self._connection = None
        self._cursor = None
        self._job = None
    
    @property
    def connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(JOBS_DB)
        return self._connection

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self.connection.cursor()
        return self._cursor

    @property
    def job(self):
        if self._job is None:
            self._job = CronJob.get(self.cursor, self.job_id)
        return self._job

    def start(self):
        job_id = Proc.start(self.account_id, 'domino', 'cleaning')
        start_job(job_id)
        self.message(f'Запущена задача {job_id}')

    def print_manually(self):
        table = self.table('table', hole_update=True).mt(1)
        toolbar = self.toolbar('toolbar')
        toolbar.item().button('Запуск в ручном режиме').onclick('.start').primary()

    def print_schedule(self):
        table = self.table('table', hole_update=True).mt(1).css('table-borderless')
        row = table.row()
        row.text('Дни по расписанию')
        row.input(name='days', value = self.job.days)
        row = table.row()
        row.text('Время запуска')
        row.input(name='time', value = str(self.job.times))
        toolbar = self.toolbar('toolbar')
        toolbar.item().css('ml-auto').button('Изменить параметры').onclick('.change').primary()

    def open(self):
        self.title('Чистка системы')
        x = self.text_block()
        x.text('Краткое описание работы системы')
        #x.header('Расписание')
        
        x.newline()
        x.newline('wdwddwd')
        x.text('wdwdwdwdwdw')
        x.text('wdwdwdwefwefwefwfwe')
        #x.header('Параметры')
        x.text('wdwdwdwefwefwefwfwe')
        x.text('wdwdwdwefwefwefwfwe')
        #x.header('Запуск')

        #tabs.print(self)

class Job(Proc.Job):
    def __init__(self, ID):
        super().__init__(ID)

    def __call__(self):
        self.log('start')
        for count in range(10):
            self.log(f'{count}')
            log.debug(f'{count}')
            self.check_for_break()
            log.debug(f'I')
            sleep(2)
            log.debug(f'II')
        self.log('stop')

if __name__ == '__main__':
    log.debug(f'{sys.argv}')
    ID = sys.argv[1]
    try:
        with Job(ID) as job:
            job()
    except:
        log.exception(__name__)
