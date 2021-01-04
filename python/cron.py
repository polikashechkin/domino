#!/usr/bin/env python3.6
import os, sys, time, sqlite3, pickle, datetime
from domino.core import log, start_log
from domino.jobs import Job, start_job, query_job, JOBS_DB, JobReport
from domino.crontab import CronTab, CronJob
from domino.cli import arg, print_error

TIMEOUT = 60

class TodayJobs:
    def __init__(self, cron_job):
        self.cron_job = cron_job
        self.jobs = {}
        self.modify_time = datetime.datetime.now()

    def load(self):
        msg = []
        TODAY = datetime.date.today()
        with sqlite3.connect(JOBS_DB) as conn:
            cur = conn.cursor()
            for job in CronJob.findall(cur, 'enabled=1'):
                if not job.days.match(TODAY):
                    msg.append(f'-{job} Не тот день')
                    continue
                if job.start is not None and job.start >= TODAY:
                    msg.append(f'-{job} Уже запущен')
                    continue
                msg.append(f'+{job}')
                self.jobs[job.rowid] = job
        msg.append(f'Всего отобрано {len(self.jobs)}')
        return ', '.join(msg)

    def log_started_job(self, job, time_ms):
        started_jobs_file = self.cron_job.get_param('started_jobs_file')
        msg = f'{datetime.datetime.now()}\t{job.rowid}\t{time_ms}\t{job.product_id}\t{job.program}\t{job.account_id}'
        with open(started_jobs_file, "a") as f:
            f.write(msg)

    def start_cycle(self):
        started = []
        for rowid, job in self.jobs.items():
            TIME = datetime.datetime.now().time()
            if job.times.match(TIME):
                started.append(rowid)
                try:
                    start = datetime.datetime.now()
                    job_id = job.start_job()
                    time_ms = (datetime.datetime.now() - start).total_seconds() / 1000
                    self.log_started_job(job, time_ms)
                    self.cron_job.log(f'Запущена процедура "{job.rowid}, {job.fullname}" как задача "{job_id}"')
                except BaseException as ex:
                    start_log.exception(f'TodayJobs().start_cycle')
                    self.cron_job.log(f'Ошибка при запуске процедуры "{job.fullname}" : {ex}')
        for rowid in started:
            del self.jobs[rowid]
            self.cron_job.log(f'Процедура "{rowid}" удалена из списка процедур дня')

if __name__ == "__main__":
    ID = arg(1)
    try:
        start_log.info(f'{ID} : cron')
        with Job.open(ID) as job:
            job.start_and_stop_previous('cron')
            started_jobs_file = os.path.join(job.folder, 'started_jobs_file.txt')
            job.set_params(started_jobs_file = started_jobs_file)

            now = datetime.datetime.now()    
            today_jobs = TodayJobs(job)
            msg = today_jobs.load()
            job.log(f'НАЧАЛО : {now} : {msg}')
            while True:
                job.check_for_break()
                now = datetime.datetime.now()
                if today_jobs.modify_time.date() != now.date():
                    # перегружаем список задач на день, если день изменился
                    now = datetime.datetime.now()    
                    today_jobs = TodayJobs(job)
                    msg = today_jobs.load()
                    job.log(f'НОВЫЙ ДЕНЬ {now.day} : {now} : {msg}')

                elif today_jobs.modify_time.hour != now.hour:
                    # перегружаем список задач каждый час
                    now = datetime.datetime.now()    
                    today_jobs = TodayJobs(job)
                    msg = today_jobs.load()
                    job.log(f'НОВЫЙ ЧАС {now.hour} : {now} : {msg}')
                #else:
                #    job.log(f'Обновление (каждый раз) {now}')
                #    today_jobs = TodayJobs(job)

                today_jobs.start_cycle()

                time.sleep(TIMEOUT)
    except:
        start_log.exception('cron')

