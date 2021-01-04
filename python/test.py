
from sqlalchemy import Column, Integer, String
from domino.databases.accountdb import AccountDb, JSON

class Database(AccountDb.Base):

    __tablename__ = 'databases'

    account_id  = Column(String, primary_key=True)
    id          = Column(String, primary_key=True)
    scheme      = Column(String)
    host        = Column(String)
    service_name = Column(String)
    port        = Column(Integer)
    info        = Column(JSON)

class Dept(AccountDb.Base):

    __tablename__ = 'depts'

    guid    = Column(String, primary_key = True)
    account_id  = Column(String)
    info    = Column(JSON)


ACCOUNTDB = AccountDb.Pool().Session()

dept = ACCOUNTDB.query(Dept).get('15f9350f-ec96-40fe-b76b-8d6ec282df6b 00674812')
print(dept)
