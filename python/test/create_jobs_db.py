import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

import domino.jobs
import domino.crontab

if __name__ == "__main__":
    print('Создание базы данных JOBS.DB')

    #if os.path.isfile(domino.jobs.JOBS_DB):
    #    print(f'БАЗА ДАННЫХ "{domino.jobs.JOBS_DB}" УЖЕ СУЩЕСТВУЕТ' )

    domino.jobs.create_structure()
    domino.crontab.create_structure()