#import flask, sqlite3, json, sys, datetime
#from domino.page import Page, Filter
from domino.core import log
#from domino.jobs import JobReport, remove_job, start_job, query_job2, JOBS_DB
#from domino.page import Page
from domino.jobs_pages import JobsPage

'''
TOW_DAYS = datetime.timedelta(days=2)

MODE = 'mode' 
MODE_ALL = 'all'
MODE_ACTIVE = 'active'
MODE_COMPLITE = 'complite'

domino_jobs_tabs = TabControl('domino_jobs_tabs')
domino_jobs_tabs.item('active', 'Активные задачи', 'print_active')
domino_jobs_tabs.item('latest', 'Недавние', 'print_latest_jobs')
domino_jobs_tabs.item('complite', 'Завершенные задачи', 'print_complete')
'''

class ThePage(JobsPage):
    def __init__(self, application, request):
        super().__init__(application, request)
'''
class _ThePage(Page):
    def __init__(self, application, request):
        super().__init__(application, request, controls=[domino_jobs_tabs])
        self.job_id = self.attribute('job_id')
        self.mode = self.request.args.get(MODE) 

    def delete(self):
        remove_job(self.job_id)
        jobs = self.table('jobs')
        jobs.row(self.job_id)
        self.message(f'Удалена задача "{self.job_id}"')
    
    def restart(self):
        job = JobReport(self.job_id)
        account_id = job.account_id
        product_id = job.product_id
        program = job.program

        job_id = None
        with sqlite3.connect(JOBS_DB) as conn:
            cur = conn.cursor()
            job_id = query_job2(cur, account_id, product_id, program, [])
            
        start_job(job_id)
        domino_jobs_tabs.print(self)
        self.message(f'Запущена задача "{job_id}"')

    def print_job_status(self, cell, job):
        if job.status == 0:
            # Работающие задачи
            cell.glif('spinner', css=' fa-pulse')
            if job.wait_for_break:
                cell.glif('ban', style='color:lightsalmon; margin-left:0.5rem')
        elif job.status == 200:
            # Успешно завершенные
            pass                
        elif job.status == 400:
            # Завершены с ошибкай
            if job.wait_for_break:
                cell.glif('ban', style='color:lightsalmon;')
            else:
                cell.glif('star', style="color:red")
        else:
            # Неизвестный статус
            cell.text(f'{job.status}')
            if job.wait_for_break:
                cell.glif('ban', style='color:lightsalmon; margin-left:0.5rem')

    def print_columns(self, table):
        table.column().style('width:3rem')
        table.column().text('#')
        table.column().text('Дата')
        table.column().text('Учетная запись')
        table.column().text('Процедура')
        table.column().text('Описание')
        table.column().text('')

    def print_row(self, row, job):
        self.print_job_status(row.cell(), job)
        row.href(job.id, 'pages/job', {"job_id":job.id})
        row.text(f'{job.start:%Y-%m-%d %H:%M:%S}')
        row.text(job.account_id)
        row.text(f'{job.product_id}.{job.program}')
        row.text(job.description)
        cell = row.cell()
        cell.css('text-right')
        if job.status != 0:
            cell.button('').css('mr-1').glif('trash', style='color:lightsalmon;').css('bg-white text-danger').small().onclick('.delete', {'job_id':job.id})
        cell.button('').glif('play-circle').css('bg-white text-info').small().onclick('.restart', {'job_id':job.id})

    def print_active(self):
        self.toolbar('toolbar').mt(1)
        table = self.table('table', hole_update=True).mt(0.5)
        self.print_columns(table)
        for job in JobReport.findall():
            if job.status <= 0:
                row = table.row(job.id)
                self.print_row(row, job)

    def print_latest_jobs(self):
        self.toolbar('toolbar').mt(1)
        table = self.table('table', hole_update=True).mt(0.5)
        self.print_columns(table)
        today = datetime.date.today()
        latest = today - TOW_DAYS
        for job in JobReport.findall():
            if job.start.date() > latest:
                row = table.row(job.id)
                self.print_row(row, job)

    def print_complete(self):
        toolbar = self.toolbar('toolbar').mt(1)
        finder = toolbar.item().css('ml-auto').style('width:20rem').input_group().small()
        finder.input(name='filter')
        finder.button().glif('search').onclick('.print_complete', forms=[toolbar])

        filter = Filter(self.get('filter'))

        table = self.table('table', hole_update=True).mt(0.5)
        self.print_columns(table)
        for job in JobReport.findall():
            if filter.match(job.procname, job.description) and job.status > 0:
                row = table.row(job.id)
                self.print_row(row, job)

    def open(self):
        self.title('Задачи')
        domino_jobs_tabs.print(self)



    def print_jobs(self, filter, mode):
        table = self.table('table', hole_update=True)
        self.print_columns(table)
        for job in JobReport.findall(): 
            row = table.row(job.id)
            self.print_row(row, job)
'''