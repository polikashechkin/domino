import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID
from domino.cli  import print_comment, Console, print_header, print_warning

if __name__ == "__main__":
    c = Console(__file__)
    params= {}
    params['account_id'] = c.input('account_id')
    params['type'] =  c.input('device_type')
    params['id'] = c.input('device_id')
    params['name'] =  c.input('device_name')
    params['description'] =  c.input('device_description')
    r = requests.get('https://dev.domino.ru/domino/active/python/check_workplace', params)
    print_header(r.url)
    print_warning(r.status_code)
    print_warning(r.text)



