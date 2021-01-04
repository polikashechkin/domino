import flask, sqlite3, json, sys
from domino.page import Page
from domino.core import log
from domino.crontab import CronTab

def start_job(page):
    job_args = page.get('job_args')
    product_id = page.get('product_id')
    account_id = page.get('account_id')
    program = page.get('program')

def open(page):
    page.application['navbar'](page)
    page.title('Процедуры')
        
    page.text('''
    Ручной запуск данных процедур не влияет на автоматический запуск, который все равно будет выполятся
    один раз в деть в назначенное время.
    Запуск без параметров означает выгрузку за вчерашний день для ежедневного отчета или
    за предыдущий месяц для ежемесячного отчета. Если даны указаны явно,
    то ежемесячеый отчет будет выполнятся за указанный месяц, а ежедневный отчет
    на указанную дату (включительно).
    ''')

    jobs = page.table('jobs')
    jobs.column().style('width:1em;')
    jobs.column().text('#')
    jobs.column().text('Учетная запись')
    jobs.column().text('Модуль')
    jobs.column().text('Процедура')
    jobs.column().text('Расписание')
    jobs.column().text('Ручной запуск').style('width:20em;')
    for job in CronTab().get_jobs():
        row = jobs.row(job.rowid)

        description = job.description if job.description is not None else job.program

        if job.enabled:
            row.text('')
        else:
            row.glif('star', style='color:orange;')
        row.text(job.rowid)
        row.text(job.account_id)
        row.text(job.product_id)
        row.href(description, f'{job.program}.open', {'job_id':job.rowid})
        #row.text(job.fullname)
        row.text(f'{job.days} {job.times}')

        #row.text(job.start_time)
        #self.time = str_to_time(time)
        #self.job_id = None
        #self.start_time = None
        #self.enabled = enabled 
        #self.job_id = job_id
        #self.start = start

        #row.text()
        run = row.input_group().css('input-group-sm')
        run.input('').name('job_args')
        run.button('Запуск').small().css('btn-primary').onclick(
            '.start_job', 
            {'account_id':job.account_id, 'product_id':job.product_id, 'program': job.program}, 
            [row]
            )
