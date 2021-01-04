import json
from domino.core import log
from domino.account_db import AccountDb
from sqlalchemy import Column, String, DateTime, Integer

def on_install(on_install_log):
    pass

class Database(AccountDb.Base):

    __tablename__ = 'databases'

    account_id      = Column(String, nullable=False, primary_key=True)
    database_id     = Column('id', String, nullable=False, primary_key=True)
    scheme          = Column(String, nullable=False)
    host            = Column(String, nullable=False)
    port            = Column(Integer, nullable=False)
    service_name    = Column(String)

    @property
    def user_name(self):
        return self.scheme

    @property
    def dsn(self):
        return f'{self.host}:{self.port}/{self.service_name}'

    @property
    def url(self):
        return f'oracle+cx_oracle://{self.scheme}:{self.scheme}r@{self.host}:{self.port}/?service_name={self.service_name}&encoding=UTF-8&nencoding=UTF-8' 


DatabaseTable = Database.__table__


