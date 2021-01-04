import os, sys, time, datetime, json
from domino.core import log
from domino.jobs import Proc

TIMEOUT = 60

class TodayProc:
    def __init__(self, ID, start_time, job):
        self.ID = ID
        self.start_time = start_time
        self.is_started = False
        self.job = job

    def try_start(self):
        if not self.is_started:
            if self.start_time <= datetime.datetime.now():
                Proc.start_by_id(self.ID)
                self.job.log(f'Запущена процедура "{self.ID}"')            
                self.is_started = True

class TodayProcs:
    def __init__(self, job):
        self.job = job
        self.procs = []
        self.modify_time = datetime.datetime.now()

    def load(self):
        msg = []
        TODAY = datetime.date.today()
        with Proc.connect() as conn:
            cur = conn.cursor()
            cur.execute('select ID, STATE, INFO from procs where CLASS=0')
            PROCS = cur.fetchall()
            for ID, STATE, INFO in PROCS:
                if STATE != Proc.STATE_ENABLED:
                    msg.append(f'-{ID} disabled')    
                    continue
                info = json.loads(INFO)
                TIME = info.get('TIME')
                DAYS = info.get('DAYS')
                JOB_ID, STATUS, START_DATE = Proc._last_job(cur, ID)
                if START_DATE and START_DATE >= TODAY:
                    msg.append(f'-{ID} уже был запущен')
                    continue
                day = str(TODAY.day)
                if DAYS:
                    days = DAYS.split(',')
                    if day not in days:
                        msg.append(f'-{ID} не тот день')
                        continue
                if TIME:
                    try:
                        hour, minute = TIME.split(':')
                        start_time = datetime.datetime(TODAY.year, TODAY.month, TODAY.day, int(hour), int(minute))
                    except:
                        msg.append(f'-{ID} не корректное время "{TIME}"')
                        log.exception(__name__)
                        continue
                else:
                    msg.append(f'-{ID} нет автозапуска')
                    continue
                
                self.procs.append(TodayProc(ID, start_time, self.job))
                msg.append(f'+{ID} {start_time}')
        msg.append(f'Всего отобрано {len(self.procs)}')
        return ', '.join(msg)

class Job(Proc.Job):
    def __init__(self, ID):
        super().__init__(ID)

    def __call__(self):
        now = datetime.datetime.now()    
        today_procs = TodayProcs(self)
        msg = today_procs.load()
        self.log(f'НАЧАЛО : {now} : {msg}')
        while True:
            self.check_for_break()
            now = datetime.datetime.now()
            if today_procs.modify_time.date() != now.date():
                # перегружаем список задач на день, если день изменился
                now = datetime.datetime.now()    
                today_procs = TodayProcs(job)
                msg = today_procs.load()
                self.log(f'НОВЫЙ ДЕНЬ {now.day} : {now} : {msg}')

            elif today_procs.modify_time.hour != now.hour:
                # перегружаем список задач каждый час
                now = datetime.datetime.now()    
                today_procs = TodayProcs(job)
                msg = today_procs.load()
                self.log(f'НОВЫЙ ЧАС {now.hour} : {now} : {msg}')

            for proc in today_procs.procs:
                proc.try_start()

            time.sleep(TIMEOUT)

if __name__ == "__main__":
    try:
        with Job(sys.argv[1]) as job:
            job()
    except:
        log.exception(f'{__name__}')

