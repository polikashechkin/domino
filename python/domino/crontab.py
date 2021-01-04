import sqlite3, datetime, arrow, json
from domino.jobs import query_job2, start_job, job_is_active, JOBS_DB
from domino.core import start_log, str_to_time, log
from domino.jobs import Задача

def ToString(value):
    if value is None:
        return ''
    t = type(value)
    if t == datetime.time:
        return value.strftime('%H:%M:%S')
    elif t == datetime.datetime:
        return value.strftime('%Y-%m-%d %H-%M-%S')
    elif t == datetime.date:
        return value.strftime('%Y-%m-%d')
    else:
        return str(value)
def ToBool(value):
    return bool(value)
def ToTime(value):
    if value is None:
        return None
    t = type(value)
    if t == str:
        return str_to_time(value)
    elif t == datetime.time:
        return value
    elif t == datetime.datetime:
        return value.time()
    else:
        return None
def ToDate(value):
    if value is None:
        return None
    t = type(value)
    if t == str:
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except:
            #log.exception('ToDate')
            return None
    elif t == datetime.date:
        return value
    elif t == datetime.datetime:
        return value.date()
    else:
        return None
def create_structure():
    conn = sqlite3.connect(JOBS_DB)
    conn.executescript('''
        create table if not exists crontab (
            product_id not null,
            program not null,
            account_id not null default(''),
            start,
            time not null default(time('02:00')),
            days not null default(''),
            enabled integer default(1),
            args blob default('[]'),
            job_id integer,
            info blob,
            primary key (product_id, program, account_id) 
        )
    ''')
class Days:
    def __init__(self, s):
        if s is None or s.isspace():
            self.days = None
        else:
            try:
                self.days = set(int(day) for day in s.split(','))
            except:
                self.days = None

    def match(self, date):
        if self.days is None:
            return True
        if isinstance(date, (datetime.datetime, datetime.date)):
            return date.day in self.days
        else:
            return True
    @property
    def ежедневно(self):
        return self.days is None

    def __str__(self):
        if self.days is None:
            return ''
        return ','.join([str(day) for day in sorted(self.days)])
class Times:
    def __init__(self, s):
        self.time = None
        if s is not None and not s.isspace():
            try:
                self.time = ToTime(s)
            except:
                pass

    def match(self, time):
        if self.time is None: 
            return True
        if isinstance(time, datetime.datetime):
            return time.time() >= self.time
        elif isinstance(time, datetime.time):
            return time >= self.time

    def __str__(self):
        return '' if self.time is None else self.time.strftime('%H:%M:%S')

class CronJob:
    def __init__(self, rowid, product_id, program, account_id, days, times, enabled, job_id, start):
        self.rowid = rowid
        self.product_id = product_id # модуль (string)
        self.program = program # Процедура (string)
        self.account_id = account_id # Учетная запись (string)
        self.days = Days(days) 
        self.times = Times(times) 
        self._enabled = ToBool(enabled) # bool (integer 0|1)
        self.job_id = job_id # integer
        self._start = ToDate(start) # дата последнего запуска
        self.info = {}
    def __str__(self):
        return f'CronJob({self.rowid}, {self.description}, {self.days} {self.times}, {self.start}/{self.job_id})'
    @property
    def ID(self):
        return self.rowid
    @property
    def процедура(self):
        return self.program
    @property
    def description(self):
        return self.info.get('description')
    @property
    def INFO(self):
        return json.dumps(self.info, ensure_ascii = False)
    @INFO.setter
    def INFO(self, value):
        if value is None:
            self.info = {}
        else:
            self.info = json.loads(value)
    @property
    def enabled(self):
        return self._enabled
    @enabled.setter
    def enabled(self,value):
        if value:
            self._enabled = True
        else:
            self._enabled = False
    @property
    def s_start(self):
        return ToString(self._start)
    @property
    def start(self):
        return self._start
    @staticmethod
    def get(cur, rowid):
        return CronJob.find(cur, 'rowid=?', [rowid])
    @staticmethod
    def find_proc(cur, account_id, product_id, proc_name):
        return CronJob.find(cur, f"account_id='{account_id}' and product_id='{product_id}' and program='{proc_name}'")
    @staticmethod
    def execute_select(cur, where_clause = None, params=[]):
        if where_clause is None:
            q = ''' select rowid, product_id, program, account_id, days, time, enabled, 
                job_id, start, info
                from crontab
                '''
            cur.execute(q)
            #log.debug(f'{q}')
        else:
            q = f''' select rowid, product_id, program, account_id, days, time, enabled, 
                job_id, start, info 
                from crontab where {where_clause}
                '''
            cur.execute(q, params)
            #log.debug(f'{q} [{params}]')
    @staticmethod
    def find(cur, where_clause = None, params = []):
        #log.debug(f'find(cur, where_clause = {where_clause}, params = {params})')
        CronJob.execute_select(cur, where_clause, params)
        r = cur.fetchone()
        if r is None:
            #log.debug(f'return None')
            return None
        else:
            rowid, product_id, program, account_id, DAYS, TIMES, ENABLED, job_id, s_start, INFO = r
            j = CronJob(rowid, product_id, program, account_id, DAYS, TIMES, ENABLED, job_id, s_start)
            j.INFO = INFO
            #log.debug(f'return {j}')
            return j
    @staticmethod
    def findall(cur, where_clause = None, params = []):
        jobs = []
        CronJob.execute_select(cur, where_clause, params)
        for ROWID, PRODUCT_ID, PROGRAM, ACCOUNT_ID, DAYS, TIME, ENABLED, JOB_ID, START, INFO in cur:
            job = CronJob(ROWID, PRODUCT_ID, PROGRAM, ACCOUNT_ID, DAYS, TIME, ENABLED, JOB_ID, START)
            job.INFO = INFO
            jobs.append(job)
        return jobs
    def update(self, cur):
        #log.debug(f'{self}.update() INFO="{self.INFO}"')
        params = [self.product_id, self.program, self.account_id, str(self.days), str(self.times),\
                    self._enabled, self.job_id, self.s_start, self.INFO, self.rowid]
        q='''
        update crontab set product_id = ?, program=?, account_id=?, 
        days=?, time=?, enabled=?, job_id=?, start=?, info=?
        where rowid=?
        '''
        cur.execute(q, params)
        #log.debug(f'{q} {params}')
    def save(self):
        with sqlite3.connect(JOBS_DB) as conn:
            self.update(conn.cursor())
    @property
    def fullname(self):
        return '/'.join([
            self.account_id if self.account_id is not None else '',
            self.product_id,
            self.program if self.program is not None else ''
        ])
    @property
    def h_description(self):
        h_days = 'Ежедневно' if self.days == '' else self.days
        h_description = f'{h_days}, в {self.times}.'
        if not self.    enabled:
            h_description += ' Заблокировано.'
        if self.s_start is not None:
            h_description += f' Последний запуск {self.s_start}, Задача {self.job_id}.'

        return h_description
    @property
    def h_activity(self):
        return f''
    @property
    def name(self):
        if self.account_id is None or self.account_id == '':
            return f'{self.product_id}.{self.program}'
        else:
            return f'{self.product_id}.{self.program}.{self.account_id}'
    def start_job(self):
        if self.rowid is None:
            return None
        with sqlite3.connect(JOBS_DB) as conn:
            cur = conn.cursor()
            self.job_id = query_job2(cur, self.account_id, self.product_id, self.program, [], self.info)
            self._start = datetime.date.today()
            self.update(cur)

        start_job(self.job_id)
        return self.job_id

class CronTab:
    def __init__(self):
        pass

    @staticmethod
    def is_active():
        return job_is_active('domino', 'cron')

    @staticmethod
    def parse_name(name):
        product_id = name
        account_id = None
        program = None
        if product_id.find('.') != -1:
            product_id, program = product_id.split('.', 1)
            if program.find('.') != -1:
                program, account_id = program.split('.')
        return product_id, program, account_id

    @staticmethod
    def parse_days(days_string):
        try:
            days = []
            for day_string in days_string.split(','):
                day = int(day_string)
                days.append(f'{int(day):02}')
            return ",".join(days)

        except:
            return ''
    
    @staticmethod
    def parse_time(time_string):
        DEFAULT = '02:00:00'
        try:
            hour, minute = time_string.split(':')
            hour = int(hour)
            minute = int(minute)
            second = 0
            if hour < 0 or hour > 24:
                return DEFAULT
            if minute < 0 or minute >= 60:
                return DEFAULT
            return f'{hour:02}:{minute:02}:{second:02}'
        except:
            return DEFAULT

    #def rowid(self, product_id, program, account_id):
    #    if account_id is None:
    #        account_id = ''
    #    self.cur.execute(
    #        'select rowid from crontab where product_id=? and program=? and account_id=?' ,
    #        [product_id, program, account_id]
    #        )
    #   r = self.cur.fetchone()
    #    if r is not None:
    #        return r[0]
    #    else:
    #        return None

    #def get(self, rowid):
    #    q = f'select rowid, product_id, program, account_id, days, time, enabled, job_id, start from crontab where rowid=?'
    #    self.cur.execute(q, [rowid])
    #    r = self.cur.fetchone()
    #    if r is not None:
    #        ROWID, PRODUCT_ID, PROGRAM, ACCOUNT_ID, DAYS, TIME, ENABLED, JOB_ID, START = r
    #        return CronJob(ROWID, PRODUCT_ID, PROGRAM, ACCOUNT_ID, DAYS, TIME, ENABLED == 1, JOB_ID, START)
    #   else:
    #       return None

    @staticmethod
    def find(module, proc, account_id):
        with sqlite3.connect(JOBS_DB) as conn:
            cur = conn.cursor()
            job = CronJob.find(cur, 'product_id=? and program=? and account_id=?',
                [module, proc, account_id])
        return job

    def today(self, TODAY = datetime.date.today()):
        '''
        Список всех процедур, доолжных запустится в конкретный день
        по умолчанию сегодня вне зависимости от времени их запуска
        '''
        #log.debug(f'TODAY = {TODAY}')
        jobs = []
        for job in self.get_jobs('enabled = 1'):
            #log.debug(f'job.start = {job.start}')
            if job.start is not None and job.start == TODAY:
                #log.debug(f'Проехали')
                continue
            if job.days.match(TODAY):
                jobs.append(job)
                #log.debug(f'Добавили')
        #log.debug(f'{jobs}')
        return jobs

    def get_jobs(self, where_clause = None, params = []):
        jobs = []
        with sqlite3.connect(JOBS_DB) as conn:
            cur = conn.cursor()
            jobs = CronJob.findall(cur, where_clause, params)
        return jobs

    def create_if_not_exists(self, product_id, program, account_id =None, days = None, time = '02:00:00', description = None):
        #log.debug(f'{self}.create_if_not_exists(self,{product_id},{program},{account_id},{days},{time},{description})')
        if account_id is None:
            account_id = ''
        days = CronTab.parse_days(days)
        time = CronTab.parse_time(time)
        with sqlite3.connect(JOBS_DB) as conn:
            cursor = conn.cursor()
            job = CronJob.find(cursor, 'account_id=? and product_id=? and program=?',
                [account_id, product_id, program])
            if job is not None:
                #log.debug(f'job is not None {description}')
                if description is not None:
                    job.info['description'] = description
                    #log.debug(f'job.update {job}')
                    job.update(cursor)
                    conn.commit()
            else:
                #log.debug(f'job is None')
                info = {}
                if description is not None:
                    info['description'] = description
                INFO = json.dumps(info, ensure_ascii=False)
                conn.execute('''
                    insert or ignore into crontab (product_id, program, account_id, days, time, info)
                    values (?, ?, ?, ?, ?, ?)
                    ''', [product_id, program, account_id, days, time, INFO])

    def add(self, product_id, program, account_id, days, time = '02:00:00'):
        if account_id is None:
            account_id = ''
        days = Days(days)
        time = Times(time)
        with sqlite3.connect(JOBS_DB) as conn:
            conn.execute('''
                insert or replace into crontab (product_id, program, account_id, days, time)
                values (?, ?, ?, ?, ?)
                ''', [product_id, program, account_id, str(days), str(time)])

    def remove_by_rowid(self, rowid):
        with sqlite3.connect(JOBS_DB) as conn:
            conn.execute(
                'delete from crontab where rowid=?', [int(rowid)]
                    )

    def remove(self, product_id, program = None, account_id = None):
        with sqlite3.connect(JOBS_DB) as conn:
            if program is None:
                conn.execute(
                    'delete from crontab where product_id=?', 
                    [product_id]
                    )
            elif account_id is None:
                conn.execute(
                    'delete from crontab where product_id=? and program=?', 
                    [product_id, program]
                    )
            else:
                conn.execute(
                    'delete from crontab where product_id=? and program=? and account_id=?', 
                    [product_id, program, account_id]
                    )

    def enable(self, product_id, program, account_id=''):
        with sqlite3.connect(JOBS_DB) as conn:
            if program is None:
                conn.execute('update crontab set enabled=1 where product_id=?', 
                    [product_id])
            else:
                if account_id is None:
                    account_id = ''
                conn.execute('update crontab set enabled=1 where product_id=? and program=? and account_id=?', 
                    [product_id, program, account_id])

    def enable_by_rowid(self, rowid):
        with sqlite3.connect(JOBS_DB) as conn:
            conn.execute('update crontab set enabled=1 where rowid=?', 
                [int(rowid)])

    def clean(self, product_id, program, account_id=''):
        with sqlite3.connect(JOBS_DB) as conn:
            if program is None:
                conn.execute('update crontab set job_id = null, start = null where product_id=?', 
                    [product_id])
            else:
                if account_id is None:
                    account_id = ''
                conn.execute('update crontab set job_id = null, start=null where product_id=? and program=? and account_id=?', 
                    [product_id, program, account_id])

    def clean_by_rowid(self, rowid):
        with sqlite3.connect(JOBS_DB) as conn:
            conn.execute('update crontab set job_id = null, start = null where rowid=?', 
                    [int(rowid)])

    def disable(self, product_id, program, account_id=''):
        with sqlite3.connect(JOBS_DB) as conn:
            if program is None:
                conn.execute('update crontab set enabled=0 where product_id=?', 
                [product_id])
            else:
                if account_id is None:
                    account_id = ''
                conn.execute('update crontab set enabled=0 where product_id=? and program=? and account_id=?', 
                [product_id, program, account_id])

    def disable_by_rowid(self, rowid):
        with sqlite3.connect(JOBS_DB) as conn:
            conn.execute('update crontab set enabled=0 where rowid=?', 
                [int(rowid)])

    def exists(self, product_id, program, account_id):
        with sqlite3.connect(JOBS_DB) as conn:
            cur = conn.cursor()
            cur.execute('select rowid from crontab where account_id = ? and product_id=? and program=?',\
                [account_id, product_id, program]) 
            r=cur.fetchone()
        return r[0] if r is not None else None

    #def start(self, product_id, program, account_id):
    #    rowid = self.rowid(product_id, program, account_id)
    #    if rowid is not None:
    #        ID = query_job(product_id, program, [])
    #        start_job(ID)
    #        with sqlite3.connect(JOBS_DB) as conn:
    #            conn.execute(
    #                '''update crontab set job_id=?, start=date() where rowid = ?'''
    #                , [ID, rowid])
    #    return ID

