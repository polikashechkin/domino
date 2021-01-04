import os, sys, json, sqlite3
from domino.core import log, DOMINO_ROOT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class AccountDb:
    Base = declarative_base()
    class Pool:
        def __init__(self):
            self.engine_name = 'account_db'
            path = os.path.join(DOMINO_ROOT, 'data', 'account.db')
            self.engine = create_engine(f'sqlite:///{path}')
            self.Session = sessionmaker(bind = self.engine)

        def session(self, account_id, **kwargs):
            return self.Session()

