import json
import os
import urllib
import urllib.parse
import cx_Oracle
from domino.log import log
from datetime import datetime

ENCODING = "Russian.AL32UTF8"
FIRST_USER = '8400000000000001'

class DominoConnection(cx_Oracle.Connection):
    def __init__(self, scheme, host, port=None, service_name=None):
        self.scheme = scheme.upper()
        self.host = host
        self.port = int(port) if port is not None else 1521
        self.service_name = service_name if service_name is not None else 'orcl'

        dsn = f'{self.host}:{self.port}/{self.service_name}'
        super().__init__(user = scheme, password=scheme, dsn=dsn, encoding = "UTF-8", nencoding = "UTF-8")

def get_database_resource_info(account, database_name = None):
    if database_name:
        file_name = "database.{0}.json".format(database_name)
    else:
        file_name = "database.json"

    if account is None:
        file = os.path.join('/DOMINO','resources', file_name)
        if os.path.isfile(file):
            database_file = file
    else:
        file = os.path.join('/DOMINO','accounts', account,'resources', file_name)
        if os.path.isfile(file) :
            database_file = file
        else: 
            file = os.path.join('/DOMINO','resources', file_name)
            if os.path.isfile(file):
                database_file = file
    if database_file is None: return None

    with open(database_file, "r") as f: 
        resource_info = json.load(f)
    return resource_info

def make_connection_string(account, database_name = None):
    resource_info = get_database_resource_info(account, database_name)

    uri_string = resource_info['uri']
    p = uri_string.split('//')
    if len(p) == 1:
        # scheme@192.168.x.x/orcl
        user, path = p[0].split('@')
    else:
        # oracledb://scheme@192.168.x.x/orcl
        user, path = p[1].split('@')
    return "{0}/{0}@{1}".format(user, path)

def connect(account, database_name = None):
    start = datetime.now()
    resource_info = get_database_resource_info(account, database_name)

    uri = resource_info.get('uri')
    scheme =  resource_info.get('scheme')
    host = resource_info.get('host')
    port = resource_info.get('port')
    service_name = resource_info.get('service_name')
    if port is not None:
        port = int(port)

    if uri is not None:
        #log.debug(f'uri="{uri}"')
        p = uri.split('//')
        if len(p) == 1:
            # scheme@192.168.x.x/orcl
            scheme, dsn = p[0].split('@')
        else:
            # oracledb://scheme@192.168.x.x/orcl
            scheme, dsn = p[1].split('@')

        p = dsn.split("/")
        if len(p) > 1: 
            #<host>/<service_name>
            host = p[0]
            service_name = p[1]
        else:
            #<host>
            host = p[0]

        p = host.split(':')
        if len(p) > 1:
            #<adress>:<port>
            host = p[0]
            port = int(p[1])
        else:
            #<address>
            pass

    connection = DominoConnection(scheme, host, port, service_name)
    log.debug('%s', datetime.now() - start)
    return connection

'''
def connect(account, database_name = None):
   start = datetime.now()
   conn_string = make_connection_string(account, database_name)
   log.debug(conn_string)
   conn = cx_Oracle.connect(conn_string, encoding = "UTF-8", nencoding = "UTF-8")
   log.debug('%s', datetime.now() - start)
   return conn
'''

def domino_login(conn, user_id = None):
   if user_id is None:
      user_id = FIRST_USER
   cur = conn.cursor()
   cur.execute("begin domino.login(hextoraw('{0}')); end;".format(user_id))
   cur.close()

def table_exists(cur, name):
    cur.execute(f"select count(*) from user_tables where table_name='{name.upper()}'")
    count = int(cur.fetchone()[0])
    return count != 0

