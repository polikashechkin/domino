import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID
from domino.cli  import print_comment, Console, print_header, print_warning

if __name__ == "__main__":
    c = Console(__file__)
    rs = Server.reg_server()
    account_id = c.input('Учетная запись')
    print(rs.domian_name)
    depts = rs.get('server.depts', {'account_id':account_id })
    print(rs.url)
    print(rs.status_code, rs.error)
    for dept in depts:
        print(dept)


